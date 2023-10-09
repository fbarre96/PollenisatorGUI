
source ~/.zshrc

trap_pollex() {
  if (( ${#BASH_SOURCE[@]} <= 1 )); then
    local command="$1"
    eval "pollex $command"
    # supress original command if return code is 0
    if [[ $? == 0 ]]
    then
      exec zsh #HACK: https://reespozzi.medium.com/cancel-a-terminal-command-during-preexec-zsh-function-c5b0d27b99fb
    fi
  fi
} 

if [[ $TRAP_FOR_POLLEX == "False" ]]
then
  echo "Trap settings is disabled. Use pollex to explicitly log and import commands in pollenisator."
else
  echo "Trap settings is enabled. Every command will be executed through pollenisator and will be logged / imported depending on the tools called."
  preexec_functions+=(trap_pollex)
fi

