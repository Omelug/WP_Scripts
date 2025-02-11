

 __      ____________   _________            .__        __
/  \    /  \______   \ /   _____/ ___________|__|______/  |_  ______
\   \/\/   /|     ___/ \_____  \_/ ___\_  __ \  \____ \   __\/  ___/
 \        / |    |     /        \  \___|  | \/  |  |_> >  |  \___ \
  \__/\  /  |____|____/_______  /\___  >__|  |__|   __/|__| /____  >
       \/       /_____/       \/     \/         |__|             \/


-----------------------------------------------------------------------

This tool is wrapper and tool for manage results from wordpress scans.


Database:
    important part of project is postgres database where are stored resultf
    FILE_LIST table - table for files, path format is relative path from root
    WEB  - table of wordpress webs by root wp link

wp_hub.py:
  --manual    Show help for all scripts.

wp_configpy - default configuration

Scripts:

    wp_dorker.py

      dork lists are saved in ./wordlists/dorks/ and path are saved in table

      --print_dork_lists    print saved dork lists
      --add_dork            Add dork (input manual)
      --add_dorks_auto      Add all dork list from ./wordlists/dorks/
      --scan_dork_list SCAN_DORK_LIST
                            dork list <path|name>, results in link_list and table

   wp_scanner.py
      --scan SCAN           Name of the script to run
      --script_args SCRIPT_ARGS
                            Arguments for the script
      --enum_all
      --brutal_all
      --cewl_all
      --save_cracked_all
      --scan_all            --enum_all --brutal_all --cewl_all

Help scripts:
    wp_db.py
        everything to connect to postgres database


----------------
FILE_SYSTEM
---------------
in the root are all scripts

wordlists  - wodlists for cracking and scanning (includig web specific cewl outputs and users, pass lists)
output - WPScans outputs, logs, etc

----------------
QUICK START
+++++++++++++
1/ make venv_init && source .venv/bin/activate
2/ make install
3/ make download_default_wordlists

4/ python3 ./scripts/wp_dorker.py --add_dorks_auto (add dorks to database)
5/ python3 ./scripts/wp_dorker.py --print_dork_lists  (choose dork_list, get name)
7/ python3 ./scripts/wp_dorker.py --scan_dork_list <dork list name>

#TODO this is incorrect
8/ scan - option 1 - scan one wp_link
    a/ check database, get wp_link
    b/ python ./scripts/wp_scanner --script "enum" --script_args ' --wp_link <WEB.wp_link> '
    c/ python ./scripts/wp_scanner --cewl "<WEB.wp_link>"
    d/ python ./scripts/wp_scanner --brutal "<WEB.wp_link>" "<FILE_LIST.name/FILE_LIST.path>"


OPTION 1 - scan one wp_link
    a/ python wp_scanner --enum_all
    b/ python wp_scanner --cewl_all
    c/ python wp_scanner --brutal_default_all
    / python wp_scanner --brutal_cewl_all


-----------------
FOR DEVELOPERS
+++++++++++++++++
If you want create script:
 a/ create file ./scripts/<script_name>.py
 b/ add run(<arguments>)
 c/ add create

#TODO make examples for multiple scenarios
External_tools:
    - WPScan