## SSH Browse v0.5.7
Utility for browsing ssh hosts in the terminal.

It has currently only been tested on Ubuntu 18.04 and up.
Support for Windows and other distros may vary.

## Requirements
To use SSH Browse you need to have:
- Python 3 (any version will probably work)
- SSH Client installed
- At least one host configured in `~/.ssh/config`

Optional (extended functionality):
- `$EDITOR` set in environment paths
- [tmux](https://github.com/tmux/tmux)
- [cmatrix](https://github.com/abishekvashok/cmatrix)


## Installation / Update
Navigate to the git repository directory and run:
```bash
./install.sh
```
## Uninstall
Navigate to the git repository directory and run:
```bash
./uninstall.sh
```
To also delete all user data:
```bash
./uninstall.sh -f
```

## Usage
To use SSH Browse type `ssh-browse` in the terminal or launcher.

### Key Features

#### Tmux Integration
SSH Browse provides two ways to work with multiple hosts in tmux:

1. **Tmux Panes (key: `t`)** - Opens selected hosts in split panes within a single tmux window
2. **Tmux Windows (key: `w`)** - Opens each selected host in separate tmux windows, automatically connecting via SSH and starting nested tmux sessions

#### Nested Tmux Sessions
The new tmux windows feature (`w` key) will:
- Create a separate tmux window for each selected host
- Name each window after the host
- Automatically connect to the host via SSH
- Start a nested tmux session on the remote host (tries to attach to existing session or creates new one)

You can also use the tmux windows feature directly from command line:
```bash
python3 tmux_split.py --windows host1 host2 host3
```
