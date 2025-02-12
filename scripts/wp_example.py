from input_parser import InputParser
from wp_config import CONFIG

__description__ = """"
    get_args and main functions in this format are nessasary for every script
    
    to make new script accesible, add it to wp_hub.py list
"""
#conf = CONFIG['wp_example'] # for using config, add name to CONFIG in wp_config.py

def get_args():
    parser = InputParser(usage=" Example script to change")
    parser.add_argument("--lol", type=str)

    args, unknown = parser.parse_known_args()
    return parser, args, unknown

async def main(print_help=False):
    parser, args, _ = get_args()

    if print_help:
        parser.print_help()
        exit(0)
