
wp_hub.py - only for running scripts

wp_config - cahnge this for run configuration
wp_dorker.py -
wp_db.py
wp_dorker.py
wp_enum.py
wp_scan.py

----------------
FILE_SYSTEM
+++++++++++++
in the root are all scripts

wordlists  - wodlists for cracking and scanning (includig sweb specific cewl outputs and users, pass lists)
output - WPScans outputs, logs, etc

----------------
QUICK START
+++++++++++++
1/ make venv_init && source .venv/bin/activate
2/ make install
3/ make download_default_wordlists

4/ python3 wp_dorker.py --add_dorks_auto (add dorks to database)
5/ python3 wp_dorker.py --print_dork_lists  (choose dork_list, get name)
7/ python3 wp_dorker.py --scan_dork_list <dork list name>

8/ scan - option 1 - scan one wp_link
    a/ check database, get wp_link
    b/ python wp_scanner --script "enum" --script_args ' --wp_link <WEB.wp_link> '
    c/ python wp_scanner --cewl "<WEB.wp_link>"
    d/ python wp_scanner --brute "<WEB.wp_link>" "<FILE_LIST.name/FILE_LIST.path>"

8/ scan - option 1 - scan all wp_links
OPTION 1 - scan one wp_link
    a/ python wp_scanner --enum_all
    b/ python wp_scanner --cewl_all
    c/ python wp_scanner --brute_default_all
    / python wp_scanner --brute_cewl_all

----------------
ULTRAQUICK START
+++++++++++++
#TODO - make make ultraquickstart (do automaticcaly all from quict start)

-----------------
FOR DEVELOPERS
+++++++++++++++++
If zou want create script:
 a/ create file ./scripts/<script_name>.py
 b/ add run(<arguments>)
 c/ add create

#TODO make examples for multiple scenarios
External_tools:
    - WPScan