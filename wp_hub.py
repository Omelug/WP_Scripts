import asyncio
import importlib
import sys
import argparse
from wp_log import print_e, print_ie, print_s, print_finished, input_cyan

class Hub:
    def __init__(self, sub_scripts):
        self.sub_scripts = sub_scripts

    async def run_sub_scripts(self, print_help=False):
        for script_name in self.sub_scripts:
            try:
                try:
                    print_s(f"{script_name}:")
                    script_module = importlib.import_module(script_name)
                    if not hasattr(script_module, 'main'):
                        print_ie(f"Error in {script_name}. No main function found.")
                        continue
                    await script_module.main(print_help=print_help)
                except SystemExit as e:
                    if e.code != 0:
                        print_e(f"{script_name} exited with error code {e.code}.")
                    else:
                        print_finished(f"{script_name} successfully.")
            except Exception as e:
                print_e(f"Exception occurred in {script_name}: {e}")

    # find subscript for given arguments
    #TODO wp_scanner not woking, now found scripts in ./scan_scripts
    def find_subscript_by_args(self, raw_args):
        for script_name in self.sub_scripts:
            #print(f"Checking {script_name}...")
            script_module = importlib.import_module(script_name)
            if hasattr(script_module, 'get_args'):
                _, script_args, _ = script_module.get_args()
                script_args_dict = vars(script_args)

                invalid_args = [arg for arg in raw_args if arg.lstrip('-') not in script_args_dict]
                if not all(arg.lstrip('-') in script_args_dict for arg in raw_args):
                    print_e(f"Invalid arguments for {script_name}: {', '.join(invalid_args)}")
                else:
                    print(f"Valid arguments for {script_name}:")
                    for arg in raw_args:
                        print_s(f"python3 ./{script_name.replace('.', '/')}.py {arg}")

# Prompt user to find a script with given arguments
def prompt_user():
    try:
        while True:
            response = input_cyan("Find submodule with these arguments? (Y/N): ").strip().upper()
            if response in ['Y', 'N']:
                return response == 'Y'
            else:
                print("Invalid input. Please enter 'Y' or 'N'.")
    except KeyboardInterrupt:
        print()
        return False

def get_args():
    parser = argparse.ArgumentParser(description='Run WP Hub scripts.')
    parser.add_argument('--manual', action='store_true', help='Show help for all scripts.')
    args, unknown = parser.parse_known_args()
    return args, unknown


if __name__ == '__main__':
    raw_args = sys.argv[1:]
    args, unknown = get_args()
    sub_scripts = ['scripts.wp_dorker', 'scripts.wp_scanner']
    if unknown:
        print_e(f"Unknown args for wp_hub.py: {unknown}")

        if prompt_user():
            running_hub = Hub(sub_scripts=sub_scripts)
            running_hub.find_subscript_by_args(raw_args)
            exit(0)
        else:
            print_e("Exiting due to unknown arguments.")
            exit(1)

    running_hub = Hub(sub_scripts=sub_scripts)
    asyncio.run(running_hub.run_sub_scripts(print_help=args.manual))