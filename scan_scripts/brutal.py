import hashlib
import json
import os
from urllib.parse import urlparse
from input_parser import InputParser
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import wp_db
from wp_config import CONFIG
from wp_db import get_session, Web, valid_wp_link, BrutalRun
from wp_log import print_e
from scripts.wp_scanner import run_command

def get_args(raw_args):
    parser = InputParser(description="Brutal Script")
    parser.add_argument('--wp_link', type=str, required=True, help='WordPress link for the enum script')
    parser.add_argument("--pass_list", type=str, required=True)
    parser.add_argument("--user_list", type=str, help="User list - default is from wpscan")
    parser.add_argument("--skip_no_xmlrcp", action="store_false")
    parser.add_argument('--overwrite', action="store_true")

    return parser.parse_args(raw_args.split())

async def run(raw_args):

    args = get_args(raw_args)

    if not await valid_wp_link(args.wp_link):
        print_e(f"Brutal script requires a valid WordPress link (no {args.wp_link})")
        return

    await brutal(args.wp_link, user_list=args.user_list, pass_list=args.pass_list, skip_no_xmlrcp=args.skip_no_xmlrcp, overwrite=args.overwrite)

 # update/create user list from last wpscan of wp_link
async def wpscan_get_user_list(wp_link):
    async with get_session() as session:
        web = (await session.execute(
            select(Web).filter(Web.wp_link == wp_link)
        )).scalars().first()

        if web.wpscan is None:
            print_e(f"{wp_link} has no wpscan")
            return False

        not_cracked = []
        if not web.cracked is None:
            with open(web.cracked, 'r') as up:
                not_cracked = [line.split(":")[0] for line in up if line.split(":")[1] != ""]

        user_list = f"{CONFIG['wp_hub']['wordlist_folder']}user/{urlparse(wp_link).netloc}.txt"
        with open(user_list, 'w') as f:
            for username in not_cracked:
                f.write(f"{username}\n")
        return user_list


def check_xmlrpc_enabled(json_file_path)-> (bool, str):
    #TODO multicall settings
    with open(json_file_path, 'r') as file:
        data = json.load(file)
        for finding in data.get('interesting_findings', []):
            if finding.get('type') == 'xmlrpc':
                if "XML-RPC seems to be enabled" in finding.get('to_s', ''):
                    return True, "xmlrpc"
    return False, "wp-login"


def get_file_hash(file_path):
    BUF_SIZE = 16384  # Read file in chunks
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while chunk := f.read(BUF_SIZE):
            md5.update(chunk)
    return md5.hexdigest()

# bruteforce wordpress site
async def brutal(wp_link, user_list=None, pass_list=None, skip_no_xmlrcp=False, overwrite=False):
    if user_list is None:
        user_list = await wpscan_get_user_list(wp_link)
        if user_list is False:
            return

    # get wpscan
    async with get_session() as session:
        async with session.begin():
            wpscan = (await session.execute(
                select(Web.wpscan).where(Web.wp_link == wp_link)
            )).scalars().first()

    xml_enabled, xml_type = check_xmlrpc_enabled(wpscan)

    if not xml_enabled and skip_no_xmlrcp:
        print_e(f"{wp_link} No xmlrcp enabled, skip")
        return

    output_path = f"{CONFIG['wp_hub']['output_folder']}wpscan_brutal/{urlparse(wp_link).netloc}_{get_file_hash(pass_list)[:10]}.json"
    if os.path.exists(output_path) and not overwrite:
        print_e(f"Brutal output already exists at {output_path}")
        return

    # run WPScan bruteforce
    await run_command(
        "wpscan --url {} --password-attack {} --usernames {} --passwords {} -t {} --stealthy -f json -o {}"
        .format(wp_link, xml_type, user_list, pass_list, 20, output_path))

    async with get_session() as session:
        web_instance = (await session.execute(
            select(Web).options(selectinload(Web.file_lists)).filter_by(wp_link=wp_link)
        )).scalars().first()

        if not web_instance:
            print_e(web_instance + "is not a valid web instance")
            return

        #TODO change cracked list accroding to results
        #wp_scanner.add_cracked()
        #with open(output_path, 'r') as file:
        #    data = json.load(file)
        #    print(data.get('password_attack'))

        pass_file_list = await wp_db.get_or_create_list(session, list_type="pass", file_list_path=pass_list)
        user_file_list = await wp_db.get_or_create_list(session, list_type="user", file_list_path=user_list)

        brutal_run = BrutalRun(
            pass_list=pass_list,
            user_list=user_list,
            wp_link=wp_link,
            path=output_path
        )

        session.add(brutal_run)
        await session.commit()