#!/bin/bash

# Define paths
INSTALL_DIR="/usr/local/share/ssh-browse"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="$HOME/.ssh-browse"

# Check if running as root (for system-wide uninstall)
if [[ $EUID -ne 0 ]]; then
    echo "Running without sudo: Uninstalling for the current user only"
     INSTALL_DIR="$HOME/.local/share/ssh-browse"
     BIN_DIR="$HOME/.local/bin"
     CONFIG_DIR="$HOME/.ssh-browse"  
else
    echo "Running with sudo: Uninstalling system-wide"
fi

# Remove the ssh-browse directory if force flag is passed
if [ "$1" == "-f" ]; then
     rm -rf "$CONFIG_DIR"
fi

# Remove .json files in the config directory
rm -f "$CONFIG_DIR"/*.json

# Delete any ssh-browse data
rm -rf "$INSTALL_DIR"

# Delete any ssh-browse binaries
rm -f "$BIN_DIR/ssh-browse"
rm -f "$BIN_DIR/ssh-hosts"
rm -f "$BIN_DIR/tmux-split"