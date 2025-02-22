#!/usr/bin/python3
import os
import subprocess
import threading
import argparse
import pwd

# Used to remove dupes while keeping order
def uniqify(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def read_ssh_config(filename):
    ssh_config = {}
    #ssh_config_list = []

    with open(filename, 'r') as file:
        current_host = None
        current_config = {}
        current_category = 'Default'
        for line in file:
            # Remove leading and trailing whitespaces
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            if line.startswith('#'):
                current_category = line[2:]
                continue
            # Check if the line starts with "Host" to identify the start of a new section
            if line.startswith('Host '):
                # If a host is already being processed, save its config
                if current_host is not None:
                    ssh_config[current_host] = current_config
                    #ssh_config_list.append(current_config)
                # Extract aliases
                aliases = []
                s = line.split(' ')
                if len(s)>2:
                    for j in range(2, len(s)):
                        aliases.append(s[j])
                # Extract the host name from the line
                current_host = line.split()[1]
                current_config = {}
                current_config['Reachable'] = 'unknown'
                current_config['Category'] = current_category  
                if len(aliases) > 0: current_config['Aliases'] = ' '.join(aliases)
            else:
                # Split the line into key-value pairs
                key, value = map(str.strip, line.split(None, 1))
                # Store key-value pairs in the current host's config
                current_config[key] = value
        # Save the last host's config
        if current_host is not None:
            ssh_config[current_host] = current_config
            #ssh_config_list.append(current_config)

    #for c in ssh_config_list: print(c)
    return ssh_config


def get_values(key, ssh_config_data) -> list:
    values = []

    for k in ssh_config_data.keys():
        value = ssh_config_data[k][key]
        values.append(value)
    
    #categories = list(set(categories))
    values = uniqify(values)
    return values

def get_categories(ssh_config_data) -> list:
    categories = []

    for k in ssh_config_data.keys():
        category = ssh_config_data[k]['Category']
        categories.append(category)
    
    #categories = list(set(categories))
    categories = uniqify(categories)
    return categories

def check_reachable(config) -> bool:
    ip = config['HostName']
    command = f'ssh -o BatchMode=yes -o ConnectTimeout=5 -o PubkeyAuthentication=no -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o ChallengeResponseAuthentication=no -o StrictHostKeyChecking=no {ip} 2>&1 | fgrep -q "Permission denied"; echo $?'
    reachable = int(subprocess.check_output(command, shell=True))  
    if (reachable == 0):
        config['Reachable'] = 'yes' 
        return True
    
    config['Reachable'] = 'no'
    return False

def check_reachable_all(ssh_config_data, wait):
    # Check reachable
    threads = []
    for k in ssh_config_data.keys():
        thread = threading.Thread(target=check_reachable, args=(ssh_config_data.get(k),))
        threads.append(thread)
        thread.start()

    if wait:
        for thread in threads:
            thread.join()


def test1():
    # Locate config file
    id = os.getuid()
    user = pwd.getpwuid(id).pw_name
    config_location = f'/home/{user}/.ssh/config'

    ssh_config_data = read_ssh_config(config_location)
    
    l = get_categories(ssh_config_data)
    print (l)
    check_reachable_all(ssh_config_data, True)
    
    for k in ssh_config_data.keys():
        print(ssh_config_data[k])

def test2(args):
    # Locate config file
    config_location = '/home/' + os.getlogin() + '/.ssh/config'
    #config_location = 'testconfig'
    ssh_config_data = read_ssh_config(config_location)
    
    output = []

    if (args.ssh_ping):
        check_reachable_all(ssh_config_data, True)
    
    hostnames = get_values('HostName', ssh_config_data)
    #print(hostnames)
    
    for k in ssh_config_data.keys():
        s = k
        if args.hostnames == True:
            s += f' ({ssh_config_data[k]["HostName"]})'
        if args.ssh_ping:
            reachable = ssh_config_data[k]["Reachable"]
            if reachable == 'true':
                s = 'o ' + s
            else:
                s = 'x ' + s

        print(s)
        print(ssh_config_data)

if __name__ == '__main__':
    msg = "ssh-hosts usage"

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--categories", help = "show categories", action="store_true")
    parser.add_argument("-p", "--ssh-ping", help = "test connection to hosts", action="store_true")
    parser.add_argument("-n", "--hostnames", help = "shows the HostName value for each host", action="store_true")

    args = parser.parse_args()    
    #print(args)
    test2(args)
    #test1()