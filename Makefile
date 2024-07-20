venv_init:
	python3 -m venv .venv

venv_clean:
	rm  -rf .venv

req_save:
	pip3 freeze > requirements.txt

install:
	#pip3 install --force-reinstall git+https://github.com/Omelug/Dork_tools.git#egg=dork_tools
	pip3 install -r requirements.txt
	pip3 install git+https://github.com/Omelug/dorkScanner.git#egg=dork_scanner
	pip3 install git+https://github.com/Omelug/python_mini_modules.git#egg=input_parser

install_external_tools:
	mkdir -p ./external_tools
	sudo apt install wpscan
	git clone https://github.com/opsdisk/pagodo.git ./external_tools/pagodo
	cd ./external_tools/pagodo && pip install -r requirements.txt

download_default_wordlists:
	mkdir -p ./wordlists
	mkdir -p ./wordlists/wp_link
	mkdir -p ./wordlists/dorks
	mkdir -p ./wordlists/pass
	mkdir -p ./wordlists/user
	mkdir -p ./wordlists/cewl

	mkdir -p ./output
	mkdir -p ./output/wpscan
	mkdir -p ./output/pass
	mkdir -p ./output/user
	mkdir -p ./output/wpscan_brutal
	mkdir -p ./output/cracked

	#Dorks
	cd ./wordlists/dorks && wget -nc "https://raw.githubusercontent.com/Proviesec/google-dorks/main/cms/google-dorks-for-wordpress.txt"

quick_start:
	python3