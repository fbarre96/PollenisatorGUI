
source ~/.zshrc

trap_pollex() {
  if (( ${#BASH_SOURCE[@]} <= 1 )); then
    local command="$1"
    # Check if the command starts with "donttrap"
    if [[ "$command" == donttrap* ]]; then
      # If it starts with "donttrap," execute it without alteration
      command="${command#donttrap}"
      eval "$command"
      exec zsh #HACK: https://reespozzi.medium.com/cancel-a-terminal-command-during-preexec-zsh-function-c5b0d27b99fb
    else
      eval "pollex $command"
      exec zsh #HACK: https://reespozzi.medium.com/cancel-a-terminal-command-during-preexec-zsh-function-c5b0d27b99fb
    fi
  else
    true
  fi
} 
echo "Trap settings is enabled. Every command will be executed through pollenisator and will be logged / imported depending on the tools called."
preexec_functions+=(trap_pollex)
# turn on extended DEBUG hook behavior (necessary to suppress original commands).

