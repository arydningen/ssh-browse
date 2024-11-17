#!/usr/bin/python3
import os
import subprocess
import atexit
import curses
import curses.panel
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

def get_hosts_to_display(ssh_config_data, selected_category, search_filter):
    hosts = []
    for k, v in ssh_config_data.items():
        if selected_category != 'All' and v['Category'] != selected_category:
            continue
        if search_filter.lower() in k.lower():
            hosts.append(k)
    return hosts

def get_preview_content(filename):
    try:
        with open(filename, 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        return [f'No notes found for {filename}']
        #return [f'No notes found']

def get_help_text():
    title = "SSH Browse Help"
    content = [
        "<enter> - Connect host",
        "<space> - Select host",
        "Up/Down - Navigate hosts",
        "Left/Right - Change category",
        "1-9 - Select category",
        "a - Ping all hosts",
        "p - Ping selected hosts",
        "h - Toggle help",
        "n - Toggle notes",
        "s - Search panel",
        "e - Edit notes",
        "t - Tmux hosts",
        "d - Run demo or die",
        "q - Quit"
    ]
    return title, content

def render_header(stdscr, col1_length, col2_length, spacer, COL_HEADER):
    stdscr.addstr(0, 4, 'Hosts', COL_HEADER)
    stdscr.addstr(0, col1_length, 'Properties', COL_HEADER)
    stdscr.addstr(0, col1_length + col2_length + spacer, 'Categories', COL_HEADER)

def render_hosts(stdscr, hosts, ssh_config_data, selected_hosts, current_option, scroll_pos, top_margin, COL_ACTIVE, COL_INACTIVE, COL_UNKNOWN, COL_SELECTION, COL_ARROW):
    for i, host in enumerate(hosts):
        if ssh_config_data[host].get('Reachable') == 'yes':
            pretext = 'o '
            color = COL_ACTIVE
        elif ssh_config_data[host].get('Reachable') == 'no':
            pretext = 'x '
            color = COL_INACTIVE
        elif ssh_config_data[host].get('Reachable') == 'pinging':
            pretext = '? '
            color = COL_UNKNOWN
        else:
            pretext = '> '
            color = COL_UNKNOWN


        if host in selected_hosts:
            color = COL_SELECTION | curses.A_DIM if color == COL_INACTIVE else COL_SELECTION
            #color = COL_SELECTION if color == COL_ACTIVE else COL_SELECTION | curses.A_DIM
        
        if i + top_margin < stdscr.getmaxyx()[0] - 1:
            stdscr.addstr(i + top_margin, 4, pretext + host, color)
            if current_option == i + scroll_pos:
                stdscr.addstr(i + top_margin, 1, '->', COL_ARROW)


def render_properties(stdscr, ssh_config_data, hosts, current_option, top_margin, col1_length, COL_PROPERTIES,COL_UNKNOWN, COL_ACTIVE, COL_INACTIVE):
    hostname = hosts[current_option]
    selected_host_config = ssh_config_data[hostname]
    propertylist = list(selected_host_config.keys())
    valuelist = list(selected_host_config.values())
    hostcolor = COL_ACTIVE if selected_host_config.get('Reachable') == 'yes' else COL_INACTIVE if selected_host_config.get('Reachable') == 'no' else COL_UNKNOWN
    stdscr.addstr(0 + top_margin, col1_length, hostname, hostcolor)

    # Remove 'Category' and 'Reachable' from propertylist and valuelist
    if 'Category' in propertylist:
        index = propertylist.index('Category')
        propertylist.pop(index)
        valuelist.pop(index)
    if 'Reachable' in propertylist:
        index = propertylist.index('Reachable')
        propertylist.pop(index)
        valuelist.pop(index)
        
    for i, (prop, val) in enumerate(zip(propertylist, valuelist)):
        stdscr.addstr(i + 1 + top_margin, col1_length, f'{prop}: {val}', COL_PROPERTIES)

def render_categories(stdscr, ssh_config_data, hosts, current_option, categories, selected_category, top_margin, col1_length, col2_length, spacer, COL_SELECTED_CATEGORY, COL_CATOGORY):
    selected_host_category = ssh_config_data[hosts[current_option]]['Category']
    for i, category in enumerate(categories):
        color = COL_SELECTED_CATEGORY if category == selected_host_category or category == selected_category else COL_CATOGORY
        stdscr.addstr(i + top_margin, col1_length + col2_length + spacer, f'{i + 1}. {category}', color)

def render_footer(stdscr, ssh_config_data, size, COL_FOOTER):
    number_of_hosts = len(ssh_config_data)
    ssh_agent_running = 'yes' if os.environ.get('SSH_AUTH_SOCK') else 'no'
    hosts_online = len([host for host in ssh_config_data if ssh_config_data[host].get('Reachable') == 'yes'])
    hosts_offline = len([host for host in ssh_config_data if ssh_config_data[host].get('Reachable') == 'no'])
    hosts_unknown = len([host for host in ssh_config_data if ssh_config_data[host].get('Reachable') == 'unknown'])
    
    stdscr.addstr(size.lines - 1, 1, "<enter> - connect | h - help | q - quit", COL_FOOTER)
    stdscr.addstr(size.lines - 2, 1, f"Online: {hosts_online}, Offline: {hosts_offline}, Unknown: {hosts_unknown}, Agent: {ssh_agent_running}", COL_FOOTER)

def render_help_panel(stdscr, title, content, COL_WINDOW, COL_TITLE, COL_CONTENT, panel=None):
    size = stdscr.getmaxyx()
    win_height = len(content) + 4
    win_width = max(len(title), max(len(line) for line in content)) + 4
    win_y = (size[0] - win_height) // 2
    win_x = (size[1] - win_width) // 2
    win_x = 15
    win_y = 1

    if panel is None:
        win = curses.newwin(win_height, win_width, win_y, win_x)
        win.bkgd(' ', COL_WINDOW)
        win.box()
        panel = curses.panel.new_panel(win)
    else:
        win = panel.window()
        win.erase()
        win.box()

    win.addstr(1, (win_width - len(title)) // 2, title, COL_TITLE)

    for i, line in enumerate(content):
        win.addstr(3 + i, 2, line, COL_CONTENT)

    return panel

def render_preview_panel(stdscr, title, content, COL_WINDOW, COL_TITLE, COL_CONTENT,x, width, height, panel=None):
    size = stdscr.getmaxyx()
    win_height = height
    win_width = width   # Fixed width
    win_y = 1
    win_x = x

    if panel is None:
        win = curses.newwin(win_height, win_width, win_y, win_x)
        win.bkgd(' ', COL_WINDOW)
        win.box()
        panel = curses.panel.new_panel(win)
    else:
        win = panel.window()
        win.erase()
        win.box()

    win.addstr(1, (win_width - len(title)) // 2, title, COL_TITLE)

    # Cut lines to fit the window width
    wrapped_content = []
    for line in content:
        while len(line) > win_width - 4:
            wrapped_content.append(line[:win_width - 4])
            line = line[win_width - 4:]
        wrapped_content.append(line)

    for i, line in enumerate(wrapped_content[:win_height - 4]):
        win.addstr(3 + i, 2, line, COL_CONTENT)

    win.box()
    return panel

def render_search_panel(stdscr, title, COL_WINDOW, COL_TITLE, COL_CONTENT, panel=None):
    size = stdscr.getmaxyx()
    win_height = 3
    win_width = size[1] - 4
    win_y = size[0] - win_height - 2
    win_x = 2

    if panel is None:
        win = curses.newwin(win_height, win_width, win_y, win_x)
        win.bkgd(' ', COL_WINDOW)
        win.box()
        panel = curses.panel.new_panel(win)
    else:
        win = panel.window()
        win.erase()
        win.box()

    win.addstr(1, 2, title, COL_TITLE)

    return panel

def init_colors():
    fgcols = []
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
        fgcols.append(curses.color_pair(i))
    return fgcols

class Theme:
    def __init__(self, theme_name='modern_theme'):
        self.theme_name = theme_name
        self.colors = self.load_theme(theme_name)

    def load_theme(self, theme_name):
        with open(get_themes_location(), 'r') as file:
            themes = json.load(file)
        return themes.get(theme_name, themes['modern_theme'])

    def init_colors(self):
        fgcols = {}
        curses.start_color()
        curses.use_default_colors()
        for index, (name, color) in enumerate(self.colors.items(), start=1):
            curses.init_pair(index, color[0], color[1])
            fgcols[name] = curses.color_pair(index)
        return fgcols

# MARK: main
def main(stdscr):
    # Load configuration from .ssh-browse file
    with open(get_config_location(), 'r') as config_file:
        config = json.load(config_file)

    # Extract settings from the configuration
    ping_on_startup = config.get('ping_on_startup', 'default_value')
    theme = Theme(config.get('theme', 'plain_theme'))
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
    exit_command = ''

    help_panel = None
    help_panel_visible = False

    preview_panel = None
    preview_panel_visible = False
    preview_content = []

    search_panel = None
    search_panel_visible = False
    search_filter = ''

    notes_dir = config.get('notes_dir', '~/.ssh-browse/')
    notes_dir = os.path.expanduser(notes_dir)

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
    selected_category = 'All'
    marked_hosts = []

    while True:
        hosts = get_hosts_to_display(ssh_config_data, selected_category, search_filter)
        stdscr.erase()
        size = os.get_terminal_size()
        last_option = current_option

        render_header(stdscr, col1_length, col2_length, spacer, COL_HEADER)
        max_lines = size.lines - top_margin - 2
        current_option = min(current_option, len(hosts) - 1)
        scroll_pos = (current_option % max_lines) + 1 if current_option >= max_lines else 0

        if len(hosts) > 0:
            render_hosts(stdscr, hosts[scroll_pos:], ssh_config_data, marked_hosts, current_option, scroll_pos, top_margin, COL_ACTIVE, COL_INACTIVE, COL_UNKNOWN, COL_SELECTION, COL_ARROW)
            render_properties(stdscr, ssh_config_data, hosts, current_option, top_margin, col1_length, COL_PROPERTIES, COL_UNKNOWN, COL_ACTIVE, COL_INACTIVE)
        
            render_categories(stdscr, ssh_config_data, hosts, current_option, categories, selected_category, top_margin, col1_length, col2_length, spacer, COL_SELECTED_CATEGORY, COL_CATOGORY)
        render_footer(stdscr, ssh_config_data, size, COL_FOOTER)
        
        if help_panel_visible:
            title, content = get_help_text()
            help_panel = render_help_panel(stdscr, title, content, COL_ACTIVE, COL_HEADER, COL_ACTIVE, help_panel)
        else:
            if help_panel:
                help_panel.hide()
                help_panel = None
        
        if preview_panel_visible:
            win_length = size.columns - col1_length - 4
            win_height = size.lines - 4
            preview_panel = render_preview_panel(stdscr, "Notes preview", preview_content, COL_ACTIVE, COL_HEADER, COL_ACTIVE, col1_length, win_length, win_height, preview_panel)
        else:
            if preview_panel:
                preview_panel.hide()
                preview_panel = None

        if search_panel_visible:
            search_panel = render_search_panel(stdscr, f"Search: {search_filter}", COL_ACTIVE, COL_HEADER, COL_ACTIVE, search_panel)
        else:
            if search_panel:
                search_panel.hide()
                search_panel = None

        curses.panel.update_panels()

        # Refresh the screen
        stdscr.move(0, 0)
        stdscr.refresh()

        stdscr.timeout(500)
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

        # Handle search input if search panel is visible
        if search_panel_visible:
            if action == curses.KEY_BACKSPACE:
                if len(search_filter) == 0:
                    search_panel_visible = False
                search_filter = search_filter[:-1]
            elif action == curses.KEY_ENTER or action == ord('\n'):
                search_panel_visible = False
            elif action >= 32 and action <= 126:
                search_filter += chr(action)
            hosts = get_hosts_to_display(ssh_config_data, selected_category, search_filter)
            continue

        if action == ord(' '):
            hostname = hosts[current_option]
            if ssh_config_data[hostname].get('Reachable') != 'pinging':
                if hostname in marked_hosts:
                    marked_hosts.remove(hostname)
                else:
                    marked_hosts.append(hostname)
        elif action == ord("\n"):
            hostname = hosts[current_option]
            if ssh_config_data[hostname].get('Reachable') == 'unknown':
                ssh_config_data[hostname]['Reachable'] = 'pinging'
                ssh_hosts.check_reachable(ssh_config_data[hostname])
            if ssh_config_data[hostname].get('Reachable') == 'yes':
                exit_command = f'ssh {hostname}'
                break
            else:
                stdscr.addstr(size.lines - 1, 1, f"Host {hostname} is not reachable", COL_FOOTER)
        elif action >= ord('1') and action <= ord('9'):
            selected_category = categories[action - ord('1')]
        elif action == ord('t'):
            tmux_split.open_ssh_hosts(marked_hosts)
            marked_hosts = []
        elif action == ord('d'):
            tmux_split.demo()
        elif action == ord('a'):
            visible_hosts = get_hosts_to_display(ssh_config_data, selected_category, search_filter)
            for hostname in visible_hosts:
                ssh_config_data[hostname]['Reachable'] = 'pinging'
            ssh_hosts.check_reachable_all({hostname: ssh_config_data[hostname] for hostname in visible_hosts}, False)
        elif action == ord('p'):
            selected_host = hosts[current_option]
            if selected_host not in marked_hosts:
                marked_hosts.append(selected_host)
            filtered_hosts = {hostname: ssh_config_data[hostname] for hostname in marked_hosts}
            for hostname in filtered_hosts:
                ssh_config_data[hostname]['Reachable'] = 'pinging'
            ssh_hosts.check_reachable_all(filtered_hosts, False)
            marked_hosts.clear()

        elif action == ord('h'):
            help_panel_visible = not help_panel_visible
        elif action == ord('s'):
            search_panel_visible = not search_panel_visible            
        elif action == ord('e'):
            hostname = hosts[current_option]
            editor = os.environ.get('EDITOR')
            exit_command = f'{editor} {notes_dir}{hostname}'
            subprocess.run(exit_command, shell=True)
            exit_command = 'ssh-browse'
            break
        elif action == ord('n'):
            preview_panel_visible = not preview_panel_visible
            if preview_panel_visible:
                hostname = hosts[current_option]
                preview_content = get_preview_content(f'{notes_dir}{hostname}')
        elif action == ord('q'):
            break
        if current_option != last_option:
            if preview_panel_visible:
                hostname = hosts[current_option]
                preview_content = get_preview_content(f'{notes_dir}{hostname}')
                preview_panel = None

    # Cleanup    
    stdscr.keypad(0)
    curses.curs_set(1)
    curses.echo()
    curses.nocbreak()

    if exit_command:
        atexit.register(os.system, exit_command)

if __name__ == "__main__":
    curses.wrapper(main)
