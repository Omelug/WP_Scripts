import asyncio
import importlib.util
import json
import os
from urllib.parse import urlparse
from input_parser import InputParser
from sqlalchemy import update, select

from wp_config import CONFIG
from wp_db import Web, get_session, getWeb_whereNull
from wp_log import print_e, print_ok

conf = CONFIG['wp_scanner']

def get_args():
    parser = InputParser()

    parser.add_argument('--scan', type=str, help='Name of the script to run')
    parser.add_argument('--script_args', type=str, default="", help='Arguments for the script')


    #parser.add_argument("--enum", type=str, help="<Web.wp_link> WPScan")
    #parser.add_argument("--brute", type=str,  help="<Web.wp_link> brute")
    #parser.add_argument("--cewl", type=str, help="<Web.wp_link> cewl")
    #parser.add_argument("--wpscan_extract", type=str, help="<Web.wpscan>")


    parser.add_argument("--enum_all", action="store_true")
    parser.add_argument("--brute_all", action="store_true")
    parser.add_argument("--cewl_all", action="store_true")
    parser.add_argument("--save_cracked_all", action="store_true")

    parser.add_argument("--scan_all", action="store_true",
                        help="--enum_all --brute_all --cewl_all")

    args, unknown = parser.parse_known_args()
    return parser, args


async def run_command(full_command, print_output=True):
    print(f"Running {full_command}")
    process = await asyncio.create_subprocess_shell(
        full_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_stream(stream, stream_name):
        if print_output:
            async for line in stream:
                print(f"{stream_name}: {line.decode().strip()}")

    stdout_task = asyncio.create_task(read_stream(process.stdout, "STDOUT"))
    stderr_task = asyncio.create_task(read_stream(process.stderr, "STDERR"))

    await process.wait()
    await stdout_task
    await stderr_task

class AsyncScanner:

    def __init__(self):
        self.queue = asyncio.Queue()

    async def worker(self):
        try:
            while True:
                try:
                    command,wp_link,script_args = await self.queue.get()
                    await scan_by_script(command,f" --wp_link {wp_link} {script_args if script_args else ''}")
                    self.queue.task_done()
                except Exception as e:
                    print(f"Error processing task {e}")
        except KeyboardInterrupt:
            print("\n You have killed workers, you bastard")

    async def start_workers(self, command, script_args=None, max_workers=conf['max_workers'], webs = None):
        if not webs:
            print_e("No webs to scan")
            return

        for web in webs:
            await self.queue.put((command,web.wp_link,script_args))

        workers = [
            asyncio.create_task(self.worker())
            for _ in range(max_workers)
        ]
        await self.queue.join()

        for worker in workers:
            worker.cancel()

async def scan_by_script(script_name, script_args):
    print_ok(f"Running script {script_name} with {script_args}")
    if not script_args:
        script_args = ""
    script_path = f"./scan_scripts/{script_name}.py"
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script {script_path} not found.")

    spec = importlib.util.spec_from_file_location(script_name, script_path)
    script_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script_module)

    if hasattr(script_module, 'run') and asyncio.iscoroutinefunction(script_module.run):
        await script_module.run(script_args)
    else:
        raise AttributeError(f"The script {script_name}.py does not have an async 'run' function.")

async def main(print_help=False):
    parser, args = get_args()
    parser.print_help() if print_help else None

    await scan_by_script(args.scan, args.script_args) if args.scan else None

    scanner = AsyncScanner()
    if args.enum_all:
        webs = getWeb_whereNull(Web.wpscan)
        await scanner.start_workers('enum',webs=webs)
    if args.brute_all:
        from scan_scripts.brutal import get_webs_without_brutal_run
        webs = await get_webs_without_brutal_run()
        await scanner.start_workers('brute',webs=webs)
    if args.cewl_all:
        from scan_scripts.cewl import webs_without_cewl
        webs = await webs_without_cewl()
        await scanner.start_workers('cewl',webs=webs)
    if args.save_cracked_all:
        await scanner.start_workers('save_cracked')
    #if args.scan_all:
    #    await scanner.start_workers('enum')
    #    await scanner.start_workers('brute')
    #    await scanner.start_workers('cewl')



if __name__ == '__main__':
    asyncio.run(main())