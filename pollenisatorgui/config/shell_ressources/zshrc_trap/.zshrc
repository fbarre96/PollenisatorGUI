
source ~/.zshrc

trap_pollex() {
  if (( ${#BASH_SOURCE[@]} <= 1 )); then
    eval "pollex $1"
    false
  else
    true
  fi
} 
echo "Trap settings is enabled. Every command will be executed through pollenisator and will be logged / imported depending on the tools called."
preexec_functions+=(trap_pollex)
# turn on extended DEBUG hook behavior (necessary to suppress original commands).

