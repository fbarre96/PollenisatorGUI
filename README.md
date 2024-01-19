![pollenisator_flat](https://github.com/AlgoSecure/Pollenisator/wiki/uploads/1e17b6e558bec07767eb12506ed6b2bf/pollenisator_flat.png)

 

## INSTALL ##

### SCRIPT

```
git clone https://github.com/fbarre96/PollenisatorGUI
cd PollenisatorGUI
./install.sh
```

### MANUAL 

#### Package required 

##### Ubuntu
```
sudo apt-get install git python3-pil python3-pil.imagetk python3-tk tmux xterm xdotool x11-xserver-utils pipx
```

##### Archlinux
```
pacman -S python tk git tmux xterm xdotool x11-xserver-utils python-pipx
```

##### Additional optional packages

Docker can be installed to fire-up a scan worker. Otherwise, your computer can be used if you have pentest tools installed (additional configuration may be required).

#### Installation :

```
git clone https://github.com/fbarre96/PollenisatorGUI
cd PollenisatorGUI
pipx install .
```

Check if you have a warning message saying that pip default install forder is out of your PATH.

If it is the case do one of these:

*  change install folder with `pip install -t '/PATH/TO/PACKAGES/' .`
*  add the install folder to your PATH
*  create a symlink/shortcut 

Once in your PATH, execute it:

```
pollenisator-gui
```


### Troubleshoot

#### _tkinter.TclError: no display name and no $DISPLAY environment variable

If you are on a native UNIX-like systme, try:
`export DISPLAY=:0.0`

#### pollenisator-gui command not found

`pipx ensurepath` then log out and relog in

