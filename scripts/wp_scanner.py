import asyncio
import importlib.util
import json
import os
from input_parser import InputParser

from wp_config import CONFIG
from wp_db import Web, getWeb_whereNull, get_webs
from wp_log import print_e

conf = CONFIG['wp_scanner']

def get_args():
    parser = InputParser()

    parser.add_argument('--scan', type=str, help='Name of scan script to run')
    parser.add_argument('--script_args', type=str, default="", help='Arguments for the scanner script')

    #parser.add_argument("--enum", type=str, help="<Web.wp_link> WPScan")
    #parser.add_argument("--brutal", type=str,  help="<Web.wp_link> brutal")
    #parser.add_argument("--cewl", type=str, help="<Web.wp_link> cewl")
    #parser.add_argument("--wpscan_extract", type=str, help="<Web.wpscan>")

    parser.add_argument("--enum_all", action="store_true", help="Run WPScan enum script on all webs")
    parser.add_argument("--brutal_all", action="store_true", help="Run brutal (bruteforce) script on all webs")
    parser.add_argument("--cewl_all", action="store_true", help="Create cewl script on all webs without cewl list")
    parser.add_argument("--save_cracked_all", action="store_true", help="Save users from wpascan to user list")

    parser.add_argument("--scan_all", action="store_true",
                        help="--enum_all --brutal_all --cewl_all")

    args, unknown = parser.parse_known_args()
    return parser, args, unknown


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

    # start async workers with command for each web
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

# one scan
async def scan_by_script(script_name, script_args=None):
    if not script_args:
        script_args = ""

    print(f"Running {script_name} with args: {script_args}")

    script_path = f"./scan_scripts/{script_name}.py"

    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Script {script_path} not found.")

    spec = importlib.util.spec_from_file_location(script_name, script_path)
    script_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script_module)

    # find run(raw_args) function in script
    if hasattr(script_module, 'run') and asyncio.iscoroutinefunction(script_module.run):
        await script_module.run(script_args)
    else:
        raise AttributeError(f"The script {script_name}.py does not have an async 'run' function.")


async def main(print_help=False):
    parser, args, unknown = get_args()

    if print_help:
        parser.print_help()
        exit(0)

    script_args = args.script_args
    if unknown:
        script_args += f" {" ".join(unknown)}"

    if args.scan:
        await scan_by_script(args.scan, script_args)

    scanner = AsyncScanner()

    if args.scan_all or args.enum_all:
        webs = await getWeb_whereNull(Web.wpscan)
        await scanner.start_workers('enum',webs=webs)

    if args.scan_all or args.brutal_all:
        webs = await get_webs() #TODO default skip_no_xmlrcp?
        await scanner.start_workers('brutal',script_args=f" --skip_no_xmlrcp {script_args} ",webs=webs)

    if args.scan_all or args.cewl_all:
        from scan_scripts.cewl import webs_without_cewl
        webs = await webs_without_cewl()
        await scanner.start_workers('cewl',webs=webs)

    if args.save_cracked_all:
        await scanner.start_workers('save_cracked')

if __name__ == '__main__':
    asyncio.run(main())