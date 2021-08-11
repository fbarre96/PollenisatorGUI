![pollenisator_flat](https://github.com/AlgoSecure/Pollenisator/wiki/uploads/1e17b6e558bec07767eb12506ed6b2bf/pollenisator_flat.png)

 

## INSTALL ##
**Prérequis** : 
```
sudo apt-get install python3-pip git python3-pil python3-tk python3-pil.imagetk
```

**Installation** :

```
git clone https://github.com/AlgoSecure/PollenisatorGUI
cd PollenisatorGUI
pip install .
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
