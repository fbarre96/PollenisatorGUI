#!/bin/bash

# Function to check if a command is available
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install packages based on the package manager
install_packages() {
    local os_type="$1"
    case "$os_type" in
        "debian" | "ubuntu")
            sudo apt-get update
            sudo apt-get install -y git python3-pil python3-pil.imagetk python3-tk tmux xterm xdotool x11-xserver-utils pipx
            ;;
        "archlinux")
            sudo pacman -Syu
            sudo pacman -S python tk git tmux xterm xdotool xorg-xrandr python-pipx
            ;;
        *)
            echo "Unsupported operating system: $os_type"
            exit 1
            ;;
    esac
}

# Detect the operating system
os_type=""
if command_exists "apt-get"; then
    os_type="debian"
elif command_exists "pacman"; then
    os_type="archlinux"
else
    echo "No procedure for your operating system . Please install required packages manually. (known packet manager are apt-get and pacman)"
    exit 1
fi

# Install required packages
echo "Installing required packages for $os_type..."
install_packages "$os_type"

# Install pipx
if ! command_exists "pipx"; then
    echo "Installing pipx..."
    python3 -m ensurepip --user
    python3 -m pip install --user pipx
fi

# Install your application using pipx
echo "Installing your application using pipx..."
pipx install . --force

echo "Installation complete!"
