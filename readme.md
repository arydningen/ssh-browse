## SSH Browse v0.5.3b
Utility for browsing ssh hosts in the terminal.

It is currently only been tested on Ubuntu 18.04 and up.
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


## Installation
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
