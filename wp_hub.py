import asyncio
import importlib
import sys

from colorama import Fore, Style

from wp_log import print_e, print_ok, print_ie, print_s, print_finished


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
        print_e("No sub-script executed successfully.")

if __name__ == '__main__':


    #check python version
    if sys.version[0] in "2":
        print_e("No support for python 2.x Use python 3.x \n")
        exit(1)

    running_hub = Hub(sub_scripts=['wp_dorker', 'wp_scanner'])
    print_help = "--help" in sys.argv or "-h" in sys.argv
    asyncio.run(running_hub.run_sub_scripts(print_help=print_help))