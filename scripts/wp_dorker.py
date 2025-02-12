import functools
import os
import shutil
from datetime import datetime
from urllib.parse import urlparse
import aiohttp
import asyncio

from bs4 import BeautifulSoup
from dork_scanner import dorkScanner
from input_parser import InputParser
from sqlalchemy import select, or_, and_
from sqlalchemy.dialects.postgresql import insert

from wp_config import CONFIG
from wp_db import get_session, Web, FileList
from wp_log import print_e, print_saved, print_ow


__description__ = """"
    For scan and manage dorks for find vulnerable wordpress sites
"""
conf = CONFIG['wp_dorker']

def get_args():
    parser = InputParser(usage=" --add_dork_wizard to add dork list\n"
                                           "\tscan with --scan_dork_list <dork_list_name>")
    parser.add_argument("--print_dork_lists", action="store_true", help="print saved dork lists")
    parser.add_argument("--add_dork_wizard", action="store_true", help="Add dork (with hints)")
    parser.add_argument("--add_dorks_auto", action="store_true", help="Add all dork list from ./wordlists/dorks/")
    parser.add_argument("--scan_dork_list", type=str, help="dork list <path|name>, results in link_list and table", required=False)

    args, unknown = parser.parse_known_args()
    return parser, args, unknown

#Check if site is wordpress
async def is_wordpress_site(url, session):
    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                text = await response.text()
                if 'wp-login.php' in text or 'wp-content/' in text:
                    return True

                soup = BeautifulSoup(text, 'html.parser')
                generator_meta = soup.find('meta', attrs={'name': 'generator'})
                if generator_meta and 'WordPress' in generator_meta.get('content', ''):
                    return True
    except aiohttp.ClientError:
        pass
    return False

# get root of wordpress site
def get_root_url(url):
    parsed_url = urlparse(url)
    root_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    return root_url

#filter onlyunique wordpress sites
async def find_unique_wordpress_instances(urls):
    unique_roots = set()
    wordpress_sites = set()

    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            root_url = get_root_url(url)
            if root_url not in unique_roots:
                unique_roots.add(root_url)
                tasks.append(is_wordpress_site(root_url, session))

        results = await asyncio.gather(*tasks)
        for root_url, is_wp in zip(unique_roots, results):
            if is_wp:
                wordpress_sites.add(root_url)

    return wordpress_sites

# Add dork list to database
async def add_dork_list(path:str, name=None, description=None):
    target_path = os.path.join('../wordlists/dorks/', os.path.basename(path))
    if not os.path.abspath(path) == os.path.abspath(target_path):
        if os.path.exists(target_path):
            print_e("File already exists in dork folder, rewriting")
        os.makedirs('../wordlists/dorks/', exist_ok=True)
        shutil.copy(path, target_path)
        print(f"File copied to {target_path}")

    async with get_session() as session:
        added_list = await session.execute(
            insert(FileList).values(
                name=name,
                path=path,
                list_type="dork",
                description=description
            ).on_conflict_do_nothing()
        )
        await session.commit()
        if added_list.rowcount == 0:
            print_e(f"No new dork - {name} already exists")

async def add_dork_wizard():
    try:
        path = input("Dork file_path: ")
        while not os.path.exists(path):
            print("Path does not exist. Please enter a valid path.")
            path = input("Dork file_path: ")
        path = os.path.relpath(path)
        print(f"Path: {path}")
        name = input("Enter the name (Press Enter to same like file): ") or None
        if name is None:
            name = os.path.splitext(os.path.basename(path))[0]
        description = input("Enter the description (Press Enter to skip): ") or None
        await add_dork_list(f"./{path}", name, description)
    except KeyboardInterrupt:
        print_e("\nDork was not saved")

# Add data from wp list to web table
async def wp_list_to_webs(session, wp_links: set):
    dork_links = (await session.execute(
        select(FileList).filter(FileList.list_type == "dork")
    )).scalars().first()

    for wp_link in wp_links:
        await session.execute(
            insert(Web).values(wp_link=wp_link).on_conflict_do_nothing()
        )

        web_entry = await session.get(Web, wp_link)
        if web_entry and web_entry not in dork_links.webs:
            web_entry.date = datetime.now()
            web_entry.list_type = "web_in_link_list"
            dork_links.webs.append(web_entry)
    await session.commit()

# scan dork list and save it to  ./wordlists/wp_link + file_list table
async def scan_dork_list( dork_list: str ,add_to_web=True):
    # get dork list by name or path
    async with get_session() as session:
        dork_list = (await session.execute(select(FileList).filter(
            and_(
            or_(FileList.name == dork_list,FileList.path == dork_list),
            FileList.list_type == "dork"
            )
        ))).scalars().first()

    if dork_list is None:
        print_e("Dork list not found by name or path ")
        return

    #link, list alredy exists? --> check if rewrite
    output_path = f"{CONFIG['wp_hub']['wordlist_folder']}wp_link/{os.path.basename(dork_list.path)}"
    if os.path.exists(output_path):
        if not conf['rewrite_link_list']:
            print_e(f"Dork {dork_list.name}:{dork_list.path} not scanned")
            print_e(f"Output {output_path} already exists")
            return
        else:
            print_ow(f"Overwriting {output_path}")

    wp_link_set = set() # scan links
    with open(dork_list.path, 'r') as file:
        dork_set = set(file.read().splitlines())
        for dork in dork_set:
            dork_whole = f"{dork} {conf['dork_filter']}"
            target = functools.partial(dorkScanner.google_search, dork_whole)
            #TODO print error requests like 429 (Too many requests)
            new_results = dorkScanner.run_pool(target=target, query=dork_whole,
                                               processes=1, pages=1, engine="bing")
            # change to only links
            for sublist in new_results:
                for url in sublist:
                    parsed_url = urlparse(url)
                    root_link = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    wp_link_set.add(root_link)

    #get only unique wordpress instances
    wp_link_set = find_unique_wordpress_instances(wp_link_set)


    # create link list file and save it ot database
    with open(output_path, 'w+') as file:
            file.write("\n".join(wp_link_set))
    print_saved(f"link list to {output_path}")

    async with get_session() as session:
        await session.execute(insert(FileList).values(
            path=output_path,
            list_type="link",
            name=f"{dork_list.name}_link"
        ).on_conflict_do_nothing())
        await session.commit()

        # add wp_links to database
        if add_to_web:
            await wp_list_to_webs(session, wp_link_set)

#print table of dork lists to stdout
async def print_dork_list_list():
    print(f"Name\t./path\t(description)")
    print("-"*60)
    async with get_session() as session:
        dork_list = await session.execute(
            select(FileList).filter(FileList.list_type == "dork")
        )
        if dork_list is None:
            print("Empty, add something with --add_dork")
        for r in dork_list.scalars().all():
            print(f"{r.name}\t{r.path}\t" + (f"({r.description})" if r.description else ""))

async def main(print_help=False):
    parser, args, _ = get_args()

    if print_help:
        parser.print_help()
        exit(0)

    # adding dork lists
    if args.print_dork_lists:
        await print_dork_list_list()
    if args.add_dork_wizard:
        await add_dork_wizard()
    if args.add_dorks_auto:
        dork_folder = './wordlists/dorks/'
        for dork_file in os.listdir(dork_folder):
            await add_dork_list(f"{dork_folder}{dork_file}", os.path.splitext(os.path.basename(dork_file))[0])

    #scanning dork list
    if args.scan_dork_list:
        try:
            await scan_dork_list(args.scan_dork_list)
        except KeyboardInterrupt:
            print_e("Dork scan was not saved")
            exit(1)


if __name__ == '__main__':
    asyncio.run(main())
