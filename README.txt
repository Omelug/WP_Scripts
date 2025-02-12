

 __      ____________   _________            .__        __
/  \    /  \______   \ /   _____/ ___________|__|______/  |_  ______
\   \/\/   /|     ___/ \_____  \_/ ___\_  __ \  \____ \   __\/  ___/
 \        / |    |     /        \  \___|  | \/  |  |_> >  |  \___ \
  \__/\  /  |____|____/_______  /\___  >__|  |__|   __/|__| /____  >
       \/       /_____/       \/     \/         |__|             \/


-----------------------------------------------------------------------

This tool is wrapper and tool for manage results from wordpress scans.

----------------
FILE_SYSTEM
---------------

wp_hub.py:
use it with arguments if you dont know what script to use, wp_hub.py will try help you
  --manual    Show help for all scripts.

wp_config.py - default configuration and management of configuration

Data:
./wordlists  - wordlists for cracking and scanning (includig web specific cewl outputs and users, pass lists)
./output - WPScans outputs, logs, etc
./external_tools - small external tools for scanning (which cant be installed with apt)

./scripts/
    wp_dorker.py

      dork lists are saved in ./wordlists/dorks/ and path are saved in table

      --print_dork_lists    print saved dork lists
      --add_dork            Add dork (input manual)
      --add_dorks_auto      Add all dork list from ./wordlists/dorks/
      --scan_dork_list SCAN_DORK_LIST
                            dork list <path|name>, results in link_list and table

   wp_scanner.py
      --scan SCAN           Name of the scan script to run
      --scanner_list        print list of available scanner scripts

      --enum_all            Run WPScan enum script on all webs
      --brutal_all          Run brutal (bruteforce) script on all webs
      --brutal_cewl_all     Run brutal with cewl links
      --cewl_all            Create cewl script on all webs without cewl list
      --save_cracked_all    Save users from wpascan to user list
      --scan_all            --enum_all --brutal_all --cewl_all

    scanner script have multiple sub_script - scan script:
    ./scan_scripts/
        brutal_cewl.py:  Bruteforce WordPress site with cewl list
        brutal.py:  Bruteforce WordPress site
        enum.py:  Enumerate WordPress site with WPScan
        cewl.py:  Generate cewl wordlists for WordPress site

Help scripts:

wp_db.py
    base functions to connect to postgres database

wp_log.py
    log IO functions for colored output

wp_secret.py (created at the begginig)
    secret vars for passwords etc. (change after first start to postgres connect)

----------------
DATABASE
---------------
important part of project is postgres database where are stored result
- path format is relative path from root

[TABLE] web: table of wordpress webs by root wp link
[TABLE] file_list: table for files - wordlists, bruteforce lists, cewl lists, user/password lists

[TABLE] cewl: additional information for cewl scans
[TABLE] web_to_list
[TABLE] brutal_run


----------------
QUICK START
+++++++++++++
1/ make quick_start

dork_list from ./wordlists/dorks:

2/ python3 ./scripts/wp_dorker.py --add_dorks_auto (add dorks to database)
3/ python3 ./scripts/wp_dorker.py --print_dork_lists  (choose dork_list, get name)
4/ python3 ./scripts/wp_dorker.py --scan_dork_list <dork list name>


5/ scan
option 1 - scan one wp_link:
    a/ check database, get wp_link
    b/ python ./scripts/wp_scanner --script "enum" --wp_link <WEB.wp_link>""
    c/ python ./scripts/wp_scanner --script "cewl" --wp_link "<WEB.wp_link>"
    d/ python ./scripts/wp_scanner --script "brutal" --wp_link "<WEB.wp_link>" --pass_list "<file_list.name/file_list.path>"


option 2 - scan all avaible wp_links
    a/ python wp_scanner --enum_all
    b/ python wp_scanner --cewl_all
    c/ python wp_scanner --brutal_default_all
    d/ python wp_scanner --brutal_cewl_all


-----------------
CREATING NEW SCIPT
-----------------
If you want create script copy wp_example.py in ./script and change it by its description

External_tools:
    - WPScan


-----------------
TODO
-----------------
- database recreation to make it cleaner ???????
- rename wp_link to web_link  or web_link to wp_link