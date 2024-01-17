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


# Function to test tkinter installation
test_tkinter () {
    timeout 1 python -m tkinter 2>&1 | grep -q "No module named '_tkinter'"
}


# Function to install python with pyenv
install_python_with_pyenv () {
    local pythonversion
    pythonversion=$(python3 --version | cut -d' ' -f2)
    env PYTHON_CONFIGURE_OPTS="--enable-shared --with-tcltk-includes=/usr/include/tcl --with-tcltk-libs=\"/usr/lib/tcl8.6 /usr/lib/tk8.6\"" pyenv install "$pythonversion"
    pyenv global "$pythonversion"
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

# Test tkinter installation
if test_tkinter; then
    if command_exists "pyenv"; then
        install_python_with_pyenv
        if test_tkinter; then
            echo "Tkinter installation failed. Please install manually python with tcl-tk support and try again."
        else
            echo "Tkinter installation successful!"
            echo "You can now run the application with the command pollenisator-gui"
        fi
    else
        echo "Tkinter installation failed. Please install pyenv or install manually python with tcl-tk support and try again."
    fi
else
    echo "Tkinter installation successful!"
    echo "You can now run the application with the command pollenisator-gui"
fi

