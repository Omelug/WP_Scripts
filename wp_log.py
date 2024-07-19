import colorama
from colorama import Fore, Style
import sys
from wp_config import CONFIG

def print_e(string, condition=True):
    if condition:
        if CONFIG['wp_hub']['color_output']:
            print(Fore.RED + string + Fore.RESET, file=sys.stderr)
        else:
            print(string, file=sys.stderr)

#nternal error, something is bad directly in the code,
# you can use it like stronger error
def print_ie (internal_err_msg):
    if CONFIG['wp_hub']['color_output']:
        print(Fore.RED + internal_err_msg + Fore.RESET, file=sys.stderr)
    else:
        print(internal_err_msg, file=sys.stderr)

def print_d(msg):
    print(Fore.GREEN + msg + Fore.RESET, file=sys.stderr)


def print_ok(msg):
    if CONFIG['wp_hub']['color_output']:
        print(Fore.CYAN + Style.BRIGHT + msg + Fore.RESET, file=sys.stderr)
    else:
        print(msg)

def print_s(msg):
     print(Fore.YELLOW + Style.BRIGHT + msg + Fore.RESET, file=sys.stderr)

def print_saved(msg):
    print(f"{Fore.GREEN} [︾] Saved {msg}{Fore.RESET}")

def print_ow(msg):
    print(f"{Fore.RED} [✐] Overwriting {msg} {Fore.RESET}")

def print_finished(msg):
    print(f"{Fore.CYAN} [✔] Finished {msg} {Fore.RESET}")