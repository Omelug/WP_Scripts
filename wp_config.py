import argparse
import configparser
import json
import os
import sys

folder_path = os.path.dirname(os.path.abspath(__file__))

config_file = "wp_secrets.ini"
if not os.path.exists(config_file):
    config = configparser.ConfigParser()
    config['DATABASE'] = {
        'username': 'postgres',
        'password': 'velmi_silne_heslo',
        'host': 'localhost',
        'port': '5432',
        'db_name': 'wp_hub_2'
    }
    config['WPSCAN'] = {
        'api_key': '<api_key>'
    }
    with open(config_file, 'w') as configfile:
        config.write(configfile)
    print(f"Please, edit {config_file}", file=sys.stderr)
    exit(0)
else:
    config = configparser.ConfigParser()
    config.read(config_file)
    db_config = config['DATABASE']
    DATABASE_URL_ASYNC = f"postgresql+asyncpg://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['db_name']}"
    WPSCAN_API = config['WPSCAN']['api_key']

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
                "db_name": db_config['db_name']

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
