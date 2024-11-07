#!/usr/bin/python3
import os
import subprocess
import atexit
import curses
import ssh_hosts
import tmux_split
import pwd

def get_config_location():
    id = os.getuid()
    user = pwd.getpwuid(id).pw_name
    return f'/home/{user}/.ssh/config'

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

def render_hosts(stdscr, hosts, ssh_config_data, selected_hosts, current_option, top_margin, COL_ACTIVE, COL_INACTIVE, COL_SELECTION, COL_ARROW):
    for i, host in enumerate(hosts):
        color = COL_ACTIVE if ssh_config_data[host].get('Reachable') == 'yes' else COL_INACTIVE
        if host in selected_hosts:
            color = COL_SELECTION if color == COL_ACTIVE else COL_SELECTION | curses.A_DIM
        pretext = 'o ' if color == COL_ACTIVE else 'x '
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

def init_colors():
    fgcols = []
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
        fgcols.append(curses.color_pair(i))
    return fgcols

def theme():
    return {
        'COL_ACTIVE': (2, -1),
        'COL_INACTIVE': (1, -1),
        'COL_HEADER': (57, -1),
        'COL_ARROW': (7, -1),
        'COL_PROPERTIES': (7, -1),
        'COL_SELECTED_CATEGORY': (7, -1),
        'COL_CATOGORY': (8, -1),
        'COL_FOOTER': (7, -1),
        'COL_SELECTION': (93, -1)
    }

def init_colors(theme_colors):
    fgcols = []
    curses.start_color()
    curses.use_default_colors()
    for index, color in enumerate(theme_colors.values(), start=1):
        curses.init_pair(index, color[0], color[1])
        fgcols.append(curses.color_pair(index))
    return fgcols


def main(stdscr):
    #fgcols = init_colors()
    #COL_ACTIVE, COL_INACTIVE, COL_HEADER, COL_ARROW, COL_PROPERTIES, COL_SELECTED_CATEGORY, COL_CATOGORY, COL_FOOTER, COL_SELECTION = fgcols[2], fgcols[1] | curses.A_DIM, fgcols[57], fgcols[7], fgcols[7], fgcols[7], fgcols[8], fgcols[7], fgcols[93]
    #COL_ACTIVE, COL_INACTIVE, COL_HEADER, COL_ARROW, COL_PROPERTIES, COL_SELECTED_CATEGORY, COL_CATOGORY, COL_FOOTER, COL_SELECTION = fgcols[2], fgcols[2] | curses.A_DIM, fgcols[2], fgcols[2], fgcols[2], fgcols[2], fgcols[2], fgcols[2], fgcols[93]
    theme_colors = theme()
    fgcols = init_colors(theme_colors)
    COL_ACTIVE, COL_INACTIVE, COL_HEADER, COL_ARROW, COL_PROPERTIES, COL_SELECTED_CATEGORY, COL_CATOGORY, COL_FOOTER, COL_SELECTION = fgcols[0], fgcols[1] | curses.A_DIM, fgcols[2], fgcols[3], fgcols[4], fgcols[5], fgcols[6], fgcols[7], fgcols[8]



    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()

    stdscr.clear()
    command = ''

    config_location = get_config_location()
    ssh_config_data = ssh_hosts.read_ssh_config(config_location)
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

        render_hosts(stdscr, hosts[scroll_pos:], ssh_config_data, selected_hosts, current_option, top_margin, COL_ACTIVE, COL_INACTIVE, COL_SELECTION, COL_ARROW)
        render_properties(stdscr, ssh_config_data, hosts, current_option, top_margin, col1_length, COL_PROPERTIES, COL_ACTIVE, COL_INACTIVE)
        render_categories(stdscr, ssh_config_data, hosts, current_option, categories, selected_category, top_margin, col1_length, col2_length, spacer, COL_SELECTED_CATEGORY, COL_CATOGORY)
        render_footer(stdscr, size, COL_FOOTER)

        stdscr.move(0, 0)
        stdscr.refresh()
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
