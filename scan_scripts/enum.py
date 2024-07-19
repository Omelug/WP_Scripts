import json
import os
from urllib.parse import urlparse
from input_parser import InputParser
from sqlalchemy import update, select
from wp_config import CONFIG
from wp_db import get_session, Web
from wp_log import print_e
from wp_scanner import run_command


async def user_extract(wp_link): #wp_link needs to be valid
    async with get_session() as session:
        user_pass_path = f"{CONFIG['wp_hub']['output_folder']}cracked/{urlparse(wp_link).netloc}.txt"
        print(f"Extracting users from {wp_link}")
        wpscan = (await session.execute(
            select(Web.wpscan).where(Web.wp_link == wp_link)
        )).scalars().first()

        with open(wpscan, 'r') as json_wscan:
            try:
                new_users = json.load(json_wscan)['users'].keys()
            except KeyError:
                print(f"No users found for {wp_link}")
                return

        old_names = []
        if os.path.exists(user_pass_path):
            with open(user_pass_path, 'r') as file:
                old_names = {line.split(':')[0] for line in file}
        with open(user_pass_path, 'a') as file:
            for user in new_users:
                if user not in old_names:
                    file.write(f"{user}:\n")

        await session.execute(
            update(Web).where(Web.wp_link == wp_link).values(cracked=user_pass_path)
        )
        await session.commit()

async def run(raw_args):
    parser = InputParser(description="Enum Script")
    parser.add_argument('--wp_link', type=str, required=True, help='WordPress link for the enum script')
    parser.add_argument('--overwrite', action="store_true")
    parser.add_argument('--api', type=str, help='WPSCan API key')
    args = parser.parse_args(raw_args.split())

    output_path = f"{CONFIG['wp_hub']['output_folder']}wpscan/{urlparse(args.wp_link).netloc}.json"
    if not args.overwrite and os.path.exists(output_path):
        print_e(f"Wordlist already exists at {output_path}")
        return

    full_command = f"wpscan --url {args.wp_link} -e vp,vt,cb,dbe,u --random-user-agent -f json -o {output_path}"
    if args.api is not None:
        full_command += f" --api-token {args.api}"

    await run_command(full_command)

    async with get_session() as session:
        await session.execute(
            update(Web).where(Web.wp_link == args.wp_link)
            .values(wpscan=output_path)
        )
        await session.commit()

    await user_extract(args.wp_link)

