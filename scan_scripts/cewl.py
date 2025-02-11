import os
from urllib.parse import urlparse
from input_parser import InputParser
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload, aliased

from wp_config import CONFIG
from wp_db import get_session, Web, FileList, CewlList, valid_wp_link, web_to_list
from wp_log import print_saved, print_e
from scripts.wp_scanner import run_command

__description__ = """ Generate cewl wordlists for WordPress site """

def get_args(raw_args):
    parser = InputParser(description="Cewl Script")
    parser.add_argument('--wp_link', type=str, required=True, help='WordPress link for the enum script')
    parser.add_argument('--overwrite', action="store_true")
    return parser.parse_args(raw_args.split())

async def run(raw_args):

    args = get_args(raw_args)

    if not await valid_wp_link(args.wp_link):
        print_e("CEWL script requires a valid WordPress link")
        return

    output_path = f"{CONFIG['wp_hub']['wordlist_folder']}cewl/{urlparse(args.wp_link).netloc}.txt"
    if not args.overwrite and os.path.exists(output_path):
        print_e(f"Wordlist already exists at {output_path}")
        return
    cewl_command = CONFIG['wp_scanner']['cewl_input'].format(output_path, args.wp_link)
    full_command = f"cewl {cewl_command}"

    await run_command(full_command)
    print_saved(f"cewl output to {output_path}")
    async with get_session() as session:

        existing_file_list = await session.execute(select(FileList).filter_by(path=output_path))
        file_list = existing_file_list.scalars().first()

        if not file_list:
            file_list = FileList(
                path=output_path,
                name=urlparse(args.wp_link).netloc,
                description="CEWL generated wordlist",
                list_type="cewl"
            )
            session.add(file_list)
        await session.commit()

        # add lists to web connection
        web_instance = (await session.execute(
            select(Web).options(selectinload(Web.file_lists)).filter_by(wp_link=args.wp_link)
        )).scalars().first()
        if file_list not in web_instance.file_lists:
            web_instance.file_lists.append(file_list)
            await session.commit()

        # insert cewl info about list
        existing_cewl_list = await session.execute(
            select(CewlList).filter_by(file_list=output_path, web_link=args.wp_link)
        )
        existing_cewl_list = existing_cewl_list.scalars().first()

        if existing_cewl_list:
            existing_cewl_list.arguments = full_command
        else:
            cewl_list = CewlList(
                file_list=output_path,
                arguments=full_command,
                web_link=args.wp_link
            )
            session.add(cewl_list)
        await session.commit()

# get from database webs that do not have cewl list yet
async def webs_without_cewl():
    async with get_session() as session:
        query = select(Web).where(
            ~exists().where(
                (Web.wp_link == web_to_list.c.web_link) &
                (web_to_list.c.list_path == FileList.path) &
                (FileList.list_type == "cewl")
            )
        )
        result = await session.execute(query)
        return result.scalars().all()