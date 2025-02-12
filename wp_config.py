import argparse
import json
import os
import sys

folder_path = os.path.dirname(os.path.abspath(__file__))

secret = "wp_secret.py"
if not os.path.exists(secret):
    with open(secret, 'w+') as f:
        print("DATABASE_URL_ASYNC = 'postgresql+asyncpg://<database username>:<password>@localhost:5432/<db_name>'", file=f)
        print(f"Please, edit {secret}", file=sys.stderr)
    exit(0)
else:
    from wp_secret import DATABASE_URL_ASYNC, WPSCAN_API

DEFAULT_CONFIG = {
            "wp_hub": {
                "folder_path": folder_path,
                "output_folder": f"./output/",
                "wordlist_folder": f"./wordlists/",
                "color_output": True,
            },
            "wp_dorker": {
                'max_search_result_urls_to_retucewlrn_per_dork': 5,
                'rewrite_link_list': True,
                'dork_filter' : "site:.cz"
            },
            "wp_db": {
                "DATABASE_URL_ASYNC": DATABASE_URL_ASYNC,
            },
            "wp_scanner": {
                'max_workers': 10,
                'cewl_input': " --min_word_length 5 --depth 1 -w {} {} ",
                'wpscan_api': WPSCAN_API,
                'skip_no_xmlrcp': True,
            }
        }

global CONFIG

def generate_default():
    with open("config.json", 'w') as f:
        json.dump(CONFIG, f, indent=4)

def load_config(config_file="config.json"):
    global CONFIG
    CONFIG = DEFAULT_CONFIG.copy()
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            file_config = json.load(f)
        CONFIG.update(file_config)
    os.makedirs(CONFIG['wp_hub']['output_folder'], mode=0o666, exist_ok=True)
    os.makedirs(CONFIG['wp_hub']['wordlist_folder'], mode=0o666, exist_ok=True)
load_config()

def get_args():
    parser = argparse.ArgumentParser(description='Run WP Hub scripts.')
    parser.add_argument('--generate_default', action='store_true', help='Generate default configuration.')
    args, unknown = parser.parse_known_args()
    return args, unknown

if __name__ == "__main__":
    args, unknown = get_args()
    if args.generate_default:
        generate_default()
