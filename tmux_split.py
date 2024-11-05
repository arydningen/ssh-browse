import os
import time
import argparse

def open_in_tmux(name, commands):
    # Get the pane-base-index setting (oh-my-tmux has base-index at 1)
    pane_base_index = int(os.popen('tmux show-option -gqv base-index').read().strip())

    os.system(f'tmux new-window -n {name}')
    for i in range(len(commands)-1):
        direction = '-v' if i%2==0 else '-h'
        os.system(f'tmux split-window {direction}')
        os.system('tmux selectl tiled')
        
    time.sleep(0.2)
    for i in range(len(commands)):
        adjusted_i = i + pane_base_index
        os.system(f'tmux send-keys -t {adjusted_i} {commands[i]}')

def open_ssh_hosts(hosts):
    commands = []
    for i in range(len(hosts)):
        commands.append(f'ssh Space {hosts[i]} Enter')
    open_in_tmux('ssh', commands)

def demo():
    colors = ['green', 'red', 'blue','white','yellow','cyan','magenta','black']
    commands = []
    for i in range(4):
        #commands.append('ssh Space tussi Enter')       
        commands.append(f'cmatrix Space -b Space -a Space -C Space {colors[i]} Enter')
    #commands.append('ssh Space fakir Enter')
    #commands.append('ssh Space dockerbuntu Enter')
    open_in_tmux('ssh1', commands)

def command_to_sendkeys(command) -> str:
    s = command.split(' ')
    s = ' Space '.join(s)
    s += ' Enter'
    return s

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filename", help = "starts each command in a separate pane")

    args = parser.parse_args()
        
        #hosts = ['dockerbuntu','zummi','tummi','fenris']
    #open_ssh_hosts(hosts)
    if args.filename:
        commands = []
        try:
            with open(args.filename, 'r', encoding='utf-8') as file:
                for line in file:
                    commands.append(command_to_sendkeys(line.rstrip()))
        except:
            print("Error could not load file!")
        finally:
            open_in_tmux('ssh', commands)
