from colorama import Fore, Style
import sys
from wp_config import CONFIG

def print_e(string, condition=True):
    if condition:
        if CONFIG['wp_hub']['color_output']:
            print(Fore.RED + string + Fore.RESET, file=sys.stderr)
        else:
            print(string, file=sys.stderr)

#Internal error, something is bad directly in the code,
#use it like stronger error
def print_ie (internal_err_msg):
    if CONFIG['wp_hub']['color_output']:
        print(Fore.RED + internal_err_msg + Fore.RESET, file=sys.stderr)
    else:
        print(internal_err_msg, file=sys.stderr)

#Debug print
def print_d(msg):
    print(Fore.GREEN + msg + Fore.RESET, file=sys.stderr)

#Print ok message
def print_ok(msg):
    if CONFIG['wp_hub']['color_output']:
        print(Fore.CYAN + Style.BRIGHT + msg + Style.RESET_ALL, file=sys.stderr)
    else:
        print(msg)

# Print input question
def input_cyan(prompt):
    if CONFIG['wp_hub']['color_output']:
        return input(Fore.CYAN + prompt + Fore.RESET).strip()
    else:
        return input(prompt).strip()

#Someshing is very good (BINGO!)
def print_s(msg):
     print(Fore.YELLOW + Style.BRIGHT + msg + Style.RESET_ALL, file=sys.stderr)

def print_saved(msg):
    print(f"{Fore.GREEN} [︾] Saved {msg}{Fore.RESET}")

# Warning message
def print_ow(msg):
    print(f"{Fore.RED} [✐] Overwriting {msg} {Fore.RESET}")

# Finished message
def print_finished(msg):
    print(f"{Fore.CYAN} [✔] Finished {msg} {Fore.RESET}")