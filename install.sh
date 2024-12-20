#!/bin/bash

# Define paths
SOURCE_DIR=$(pwd)/src  # assumes install.sh is run from the repo root
INSTALL_DIR="/usr/local/share/ssh-browse"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="$HOME/.ssh-browse"

# Check if running as root (for system-wide install)
if [[ $EUID -ne 0 ]]; then
   echo "Running without sudo: Installing for the current user only"
   INSTALL_DIR="$HOME/.local/share/ssh-browse"
   BIN_DIR="$HOME/.local/bin"
   CONFIG_DIR="$HOME/.ssh-browse"
   mkdir -p "$BIN_DIR"
else
   echo "Running with sudo: Installing system-wide"
fi

# Create the installation directory
mkdir -p "$INSTALL_DIR"

# Copy Python files to the organized directory and make them executable
FILES=("ssh_browse.py" "ssh_hosts.py" "tmux_split.py")
for file in "${FILES[@]}"; do
    if [[ -f "$SOURCE_DIR/$file" ]]; then
        cp "$SOURCE_DIR/$file" "$INSTALL_DIR"
        chmod +x "$INSTALL_DIR/$file"
        echo "Installed $file to $INSTALL_DIR"
    else
        echo "Warning: $file not found in $SOURCE_DIR"
    fi
done

# Create symlinks in the /bin directory for easy access
ln -sf "$INSTALL_DIR/ssh_browse.py" "$BIN_DIR/ssh-browse"
ln -sf "$INSTALL_DIR/ssh_hosts.py" "$BIN_DIR/ssh-hosts"

echo "Symlinks created:"
echo "  ssh-browse -> $INSTALL_DIR/ssh_browse.py"
echo "  ssh-hosts -> $INSTALL_DIR/ssh_hosts.py"

# Copy themes.json and config.json to $HOME/.ssh-browse/
mkdir -p "$CONFIG_DIR"
cp "$SOURCE_DIR/themes.json" "$CONFIG_DIR"
cp "$SOURCE_DIR/config.json" "$CONFIG_DIR"
echo "Copied themes.json and config.json to $CONFIG_DIR"

echo "Installation complete!"
echo "Make sure $BIN_DIR is in your PATH if you installed without sudo."