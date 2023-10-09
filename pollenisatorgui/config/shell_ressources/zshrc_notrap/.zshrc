
source ~/.zshrc
echo "Trap command is disabled.\nUse the Prefix command \"pollex\" to exec, log and import commands in pollenisator or activate the trap setting."
precmd_functions=(${precmd_functions:#trap_pollex})
