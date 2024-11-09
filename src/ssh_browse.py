#!/usr/bin/python3
import os
import subprocess
import atexit
import curses
import ssh_hosts
import tmux_split
import pwd
import json

# Wsl2 compatibility
def get_ssh_config_location():
    id = os.getuid()
    user = pwd.getpwuid(id).pw_name
    return f'/home/{user}/.ssh/config'

def get_config_location():
    id = os.getuid()
    user = pwd.getpwuid(id).pw_name
    return f'/home/{user}/.ssh-browse/config.json'

def get_themes_location():
    id = os.getuid()
    user = pwd.getpwuid(id).pw_name
    return f'/home/{user}/.ssh-browse/themes.json'

def get_hosts_to_display(ssh_config_data, selected_category):
    hosts = []
    for k in ssh_config_data.keys():
        if selected_category != 'All':
            if ssh_config_data[k]['Category'] == selected_category:
                hosts.append(k)
        else:
            hosts.append(k)
    return hosts

def render_header(stdscr, col1_length, col2_length, spacer, COL_HEADER):
    stdscr.addstr(0, 4, 'Hosts', COL_HEADER)
    stdscr.addstr(0, col1_length, 'Properties', COL_HEADER)
    stdscr.addstr(0, col1_length + col2_length + spacer, 'Categories', COL_HEADER)

def render_hosts(stdscr, hosts, ssh_config_data, selected_hosts, current_option, top_margin, COL_ACTIVE, COL_INACTIVE, COL_UNKNOWN, COL_SELECTION, COL_ARROW):
    for i, host in enumerate(hosts):
        if ssh_config_data[host].get('Reachable') == 'yes':
            pretext = 'o '
            color = COL_ACTIVE
        elif ssh_config_data[host].get('Reachable') == 'no':
            pretext = 'x '
            color = COL_INACTIVE
        else:
            pretext = '? '
            color = COL_UNKNOWN
        if host in selected_hosts:
            color = COL_SELECTION if color == COL_ACTIVE else COL_SELECTION | curses.A_DIM

        stdscr.addstr(i + top_margin, 4, pretext + host, color)
        if current_option == i:
            stdscr.addstr(i + top_margin, 1, '->', COL_ARROW)

def render_properties(stdscr, ssh_config_data, hosts, current_option, top_margin, col1_length, COL_PROPERTIES, COL_ACTIVE, COL_INACTIVE):
    hostname = hosts[current_option]
    selected_host_config = ssh_config_data[hostname]
    propertylist = list(selected_host_config.keys())
    valuelist = list(selected_host_config.values())
    hostcolor = COL_ACTIVE if selected_host_config.get('Reachable') == 'yes' else COL_INACTIVE
    stdscr.addstr(0 + top_margin, col1_length, hostname, hostcolor)
    for i, (prop, val) in enumerate(zip(propertylist, valuelist)):
        stdscr.addstr(i + 1 + top_margin, col1_length, f'{prop}: {val}', COL_PROPERTIES)

def render_categories(stdscr, ssh_config_data, hosts, current_option, categories, selected_category, top_margin, col1_length, col2_length, spacer, COL_SELECTED_CATEGORY, COL_CATOGORY):
    selected_host_category = ssh_config_data[hosts[current_option]]['Category']
    for i, category in enumerate(categories):
        color = COL_SELECTED_CATEGORY if category == selected_host_category or category == selected_category else COL_CATOGORY
        stdscr.addstr(i + top_margin, col1_length + col2_length + spacer, f'{i + 1}. {category}', color)

def render_footer(stdscr, size, COL_FOOTER):
    stdscr.addstr(size.lines - 2, 1, "<space> - select  | t - tmux selected   | d - demo or die", COL_FOOTER)
    stdscr.addstr(size.lines - 1, 1, "<enter> - connect | e - view/edit notes | q - quit", COL_FOOTER)

def render_centered_window(stdscr, title, content, choices, selected_choice, COL_WINDOW, COL_TITLE, COL_CONTENT, COL_CHOICES, COL_SELECTED_CHOICE, win=None):
    size = stdscr.getmaxyx()
    win_height = len(content) + len(choices) + 4
    win_width = max(len(title), max(len(line) for line in content), max(len(choice) for choice in choices)) + 4
    win_y = (size[0] - win_height) // 2
    win_x = (size[1] - win_width) // 2
    win_x = 3

    if win is None:
        win = curses.newwin(win_height, win_width, win_y, win_x)
        win.bkgd(' ', COL_WINDOW)
        win.box()

    win.clear()
    win.box()

    win.addstr(1, (win_width - len(title)) // 2, title, COL_TITLE)

    for i, line in enumerate(content):
        win.addstr(3 + i, 2, line, COL_CONTENT)

    for i, choice in enumerate(choices):
        color = COL_SELECTED_CHOICE if i == selected_choice else COL_CHOICES
        win.addstr(3 + len(content) + i, 2, choice, color)

    # stdscr.refresh()
    # win.refresh()
    return win

def init_colors():
    fgcols = []
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
        fgcols.append(curses.color_pair(i))
    return fgcols

class Theme:
    def __init__(self, theme_name='original_theme'):
        self.theme_name = theme_name
        self.colors = self.load_theme(theme_name)

    def load_theme(self, theme_name):
        with open(get_themes_location(), 'r') as file:
            themes = json.load(file)
        return themes.get(theme_name, themes['original_theme'])

    def init_colors(self):
        fgcols = {}
        curses.start_color()
        curses.use_default_colors()
        for index, (name, color) in enumerate(self.colors.items(), start=1):
            curses.init_pair(index, color[0], color[1])
            fgcols[name] = curses.color_pair(index)
        return fgcols

def main(stdscr):
    # Load configuration from .ssh-browse file
    config_file_path = get_config_location()
    #config_file_path = 'config.json'
    with open(config_file_path, 'r') as config_file:
        config = json.load(config_file)

    # Extract settings from the configuration
    ping_on_startup = config.get('ping_on_startup', 'default_value')
    
    #theme = Theme('original_theme')
    theme = Theme(config.get('theme', 'plain_theme'))


    help_window = None

    fgcols = theme.init_colors()
    COL_ACTIVE = fgcols['COL_ACTIVE']
    COL_INACTIVE = fgcols['COL_INACTIVE'] # | curses.A_DIM
    COL_UNKNOWN = fgcols['COL_UNKNOWN']
    COL_HEADER = fgcols['COL_HEADER']
    COL_ARROW = fgcols['COL_ARROW']
    COL_PROPERTIES = fgcols['COL_PROPERTIES']
    COL_SELECTED_CATEGORY = fgcols['COL_SELECTED_CATEGORY']
    COL_CATOGORY = fgcols['COL_CATOGORY']
    COL_FOOTER = fgcols['COL_FOOTER']
    COL_SELECTION = fgcols['COL_SELECTION']
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()

    stdscr.clear()
    command = ''

    # Uses wsl2 compatible path as default
    ssh_config_location = config.get('ssh_config_location', get_ssh_config_location())
    ssh_config_data = ssh_hosts.read_ssh_config(ssh_config_location)

    if ping_on_startup == 'true':
        ssh_hosts.check_reachable_all(ssh_config_data, False)

    top_margin, col1_length, col2_length, spacer = 2, 10, 20, 10
    for k in ssh_config_data.keys():
        if len(k) + spacer > col1_length:
            col1_length = len(k) + spacer

    current_option = 0
    categories = ssh_hosts.get_categories(ssh_config_data)
    categories.insert(0, 'All')
    selected_hosts = []
    selected_category = 'All'

    while True:
        hosts = get_hosts_to_display(ssh_config_data, selected_category)
        stdscr.erase()
        size = os.get_terminal_size()

        render_header(stdscr, col1_length, col2_length, spacer, COL_HEADER)
        max_lines = size.lines - top_margin - 2
        current_option = min(current_option, len(hosts) - 1)
        scroll_pos = (current_option % max_lines) + 1 if current_option >= max_lines else 0

        render_hosts(stdscr, hosts[scroll_pos:], ssh_config_data, selected_hosts, current_option, top_margin, COL_ACTIVE, COL_INACTIVE, COL_UNKNOWN, COL_SELECTION, COL_ARROW)
        render_properties(stdscr, ssh_config_data, hosts, current_option, top_margin, col1_length, COL_PROPERTIES, COL_ACTIVE, COL_INACTIVE)
        render_categories(stdscr, ssh_config_data, hosts, current_option, categories, selected_category, top_margin, col1_length, col2_length, spacer, COL_SELECTED_CATEGORY, COL_CATOGORY)
        render_footer(stdscr, size, COL_FOOTER)
        # help_window = render_centered_window(stdscr, 'SSH Browse', ['Select a host to connect to', 'Press q to quit', ''], ['good','evil'], 0, COL_ACTIVE, COL_HEADER, COL_ACTIVE, COL_ACTIVE, COL_ACTIVE, help_window)
        
        stdscr.move(0, 0)
        stdscr.refresh()
        if help_window:
            help_window.refresh()

        stdscr.timeout(1000)
        action = stdscr.getch()

        if action == curses.KEY_UP:
            current_option = max(current_option - 1, 0)
        elif action == curses.KEY_DOWN:
            current_option = min(current_option + 1, len(hosts) - 1)
        elif action == curses.KEY_RIGHT:
            category_index = categories.index(selected_category)
            selected_category = categories[(category_index + 1) % len(categories)]
        elif action == curses.KEY_LEFT:
            category_index = categories.index(selected_category)
            selected_category = categories[(category_index - 1) % len(categories)]
        elif action == ord(' '):
            hostname = hosts[current_option]
            if hostname in selected_hosts:
                selected_hosts.remove(hostname)
            else:
                selected_hosts.append(hostname)
        elif action == ord("\n"):
            hostname = hosts[current_option]
            command = f'ssh {hostname}'
            break
        elif action == ord('e'):
            hostname = hosts[current_option]
            editor = os.environ.get('EDITOR')
            command = f'{editor} ~/.ssh-browse/{hostname}'
            subprocess.run(command, shell=True)
            command = 'ssh-browse'
            break
        elif action >= ord('1') and action <= ord('9'):
            selected_category = categories[action - ord('1')]
        elif action == ord('t'):
            tmux_split.open_ssh_hosts(selected_hosts)
            selected_hosts = []
        elif action == ord('d'):
            tmux_split.demo()
        elif action == ord('p'):
            ssh_hosts.check_reachable_all(ssh_config_data, False) 
        elif action == ord('q'):
            break

    stdscr.keypad(0)
    curses.curs_set(1)
    curses.echo()
    curses.nocbreak()

    if command:
        atexit.register(os.system, command)

if __name__ == "__main__":
    curses.wrapper(main)
