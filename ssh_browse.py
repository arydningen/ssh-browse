#!/usr/bin/python3
import os
import subprocess
import atexit
import curses
import ssh_hosts
import tmux_split
import pwd

def main(stdscr):
    # Initialize color pairs
    fgcols = []
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i, i, -1)
        fgcols.append(curses.color_pair(i))

    COL_ACTIVE = fgcols[2]
    COL_INACTIVE = fgcols[1] | curses.A_DIM
    COL_HEADER = fgcols[57]
    COL_ARROW = fgcols[7]
    COL_PROPERTIES = fgcols[7]
    COL_SELECTED_CATEGORY = fgcols[7]
    COL_CATOGORY = fgcols[8]
    COL_FOOTER = fgcols[7]

    COL_SELECTION = fgcols[93]

    curses.curs_set(0)
    curses.noecho() ; curses.cbreak()

    # Clear the screen
    stdscr.clear()
    command = ''

    # Locate config file
    id = os.getuid()
    user = pwd.getpwuid(id).pw_name
    config_location = f'/home/{user}/.ssh/config'

    ssh_config_data = ssh_hosts.read_ssh_config(config_location)
    ssh_hosts.check_reachable_all(ssh_config_data, False)

    # Layout helpers
    top_margin = 2
    col1_length = 10
    col2_length = 20
    spacer = 10

    # Set the length of the host list
    for k in ssh_config_data.keys():
        if len(k)+spacer>col1_length: col1_length = len(k)+spacer

    # Set the cursor to the first option
    current_option = 0

    categories = ssh_hosts.get_categories(ssh_config_data)
    categories.insert(0, 'All')

    #categories.insert(0,'All')
    #selected_category = 'All'

    # For TMUX (at least for now)
    selected_hosts = []

    # For the selected category
    selected_category = 'All'

    # Render the window
    scroll_pos = 0
    while True:
        # Get the list of hosts to display
        hosts = []
        for k in ssh_config_data.keys():
            if selected_category != 'All':
                if ssh_config_data[k]['Category'] == selected_category:
                    hosts.append(k)
            else:
                hosts.append(k)

        # Clear the screen
        # stdscr.clear()
        stdscr.erase()
        size = os.get_terminal_size()

        # Header
        stdscr.addstr(0, 4, 'Hosts', COL_HEADER) 
        #stdscr.addstr(0, col1_length, 'Properties', headercolor | curses.A_UNDERLINE | curses.A_BOLD )
        stdscr.addstr(0, col1_length, 'Properties', COL_HEADER)
        stdscr.addstr(0, col1_length+col2_length+spacer, 'Categories', COL_HEADER )

        # Calculate scroll pos
        footer_length = 2

        # Limit the current option to the number of hosts
        if current_option >= len(hosts): 
            current_option = len(hosts)-1

        max_lines = size.lines - top_margin - footer_length
        if current_option >= max_lines:
            scroll_pos = (current_option % max_lines) + 1
        else:
            scroll_pos = 0
        
        # Render each Host
        for i in range(min( len(hosts), max_lines )):
            text = hosts[i + scroll_pos]
            if ssh_config_data[hosts[i + scroll_pos]].get('Reachable') == 'true':
                color = COL_ACTIVE
                if text in selected_hosts:
                    color = COL_SELECTION
                pretext = 'o '
            else:
                color = COL_INACTIVE
                if text in selected_hosts:
                    color = COL_SELECTION | curses.A_DIM               
                pretext = 'x '                

            text = pretext + text
            stdscr.addstr(i+top_margin, 4, text, color)
            
            if current_option == i+scroll_pos:
                text = hosts[i + scroll_pos]
                stdscr.addstr(i+top_margin, 1, '->', COL_ARROW)

        # Render properties of selected Host
        hostname = hosts[current_option]
        selected_host_config = ssh_config_data[hostname]
        propertylist = list(selected_host_config.keys())
        valuelist = list(selected_host_config.values())

        hostcolor = COL_INACTIVE

        if 'Reachable' in selected_host_config:
            if selected_host_config['Reachable'] == 'true': hostcolor = COL_ACTIVE
        
        # Selected host
        stdscr.addstr(0+top_margin, col1_length, hosts[current_option], hostcolor)

        # Host properties
        for i in range(len(propertylist)):
            s = propertylist[i] + ': ' + valuelist[i]
            stdscr.addstr(i+1+top_margin, col1_length, s, COL_PROPERTIES)

        # Render categories
        selected_host_cateogory = ssh_config_data[hosts[current_option]]['Category']
        for i in range(len(categories)):
            s = f'{i+1}. {categories[i]}'

            if categories[i] == selected_host_cateogory: 
                color = COL_SELECTED_CATEGORY 
            else: color = COL_CATOGORY

            # Special case for 'All'
            if categories[i] == 'All':
                if selected_category == 'All': 
                    color = COL_SELECTED_CATEGORY
                else:
                    color = COL_CATOGORY

            stdscr.addstr(i+top_margin, col1_length+col2_length+(spacer), s, color)

        # Bottom text
        stdscr.addstr(size.lines-2, 1, "<space> - select  | t - tmux selected   | d - demo or die", COL_FOOTER)
        stdscr.addstr(size.lines-1, 1, "<enter> - connect | e - view/edit notes | q - quit", COL_FOOTER)
        

        # Set cursor resting position
        stdscr.move(0, 0)

        stdscr.refresh()
        # Get the user's next action
        stdscr.timeout(1000)
        action = stdscr.getch()

        # Move the cursor up
        if action == curses.KEY_UP:
            current_option = max(current_option - 1, 0)
        # Move the cursor down
        elif action == curses.KEY_DOWN:
            current_option = min(current_option + 1, len(hosts) - 1)

        # Right arrow
        elif action == curses.KEY_RIGHT:
            if selected_category == None:
                selected_category = selected_host_cateogory
            else:
                category_index = categories.index(selected_category)
                selected_category = categories[(category_index + 1) % len(categories)]

        # Left arrow
        elif action == curses.KEY_LEFT:
            if selected_category == None:
                selected_category = selected_host_cateogory
            else:
                category_index = categories.index(selected_category)
                selected_category = categories[(category_index - 1) % len(categories)]

        elif action == ord(' '):
            hostname = hosts[current_option]
            if hostname in selected_hosts:
                selected_hosts.remove(hostname)              
            else:
                selected_hosts.append(hostname)

        # Select the current option
        elif action == ord("\n"):
            hostname = hosts[current_option]
            command = f'ssh {hostname}'
            break

        # Edit host notes
        elif action == ord('e'):
            hostname = hosts[current_option]
            editor = os.environ.get('EDITOR')
            command = f'{editor} ~/.ssh-browse/{hostname}' 
            subprocess.run(command, shell=True)

            command = 'ssh-browse'
            break

        # Select category
        elif action >= ord('1') and action <= ord('9'):
            if selected_category == None:
                if len(categories) > action-ord('1'):
                    selected_category = categories[action-ord('1')]
            else:
                selected_category = None
                
        # Tmux
        elif action == ord('t'):
            tmux_split.open_ssh_hosts(selected_hosts)
            selected_hosts = []
            pass
        elif action == ord('d'):
            tmux_split.demo()
            # selected_hosts = []
            pass

        elif action == ord('e'):
            command = f'editor {config_location}'
            break
        elif action == ord('q'):
            break
    
    # End program - Restore terminal settings
    stdscr.keypad(0)
    curses.curs_set(1)
    curses.echo()
    curses.nocbreak()        
    # curses.endwin() # This is not needed when using wrapper

    # Run any command after ending the curse window
    if command != '':
        #print(f'Running command: {command}')
        atexit.register(os.system, command)

if __name__ == "__main__":
    curses.wrapper(main)
