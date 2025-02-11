SHELL := /bin/zsh

ifndef VERBOSE
.SILENT:
endif

venv_init:
	if [ -d ".venv" ]; then \
		 echo "\033[38;5;214m.venv already exists,";\
		 echo "run venv_clean before for refresh\033[0m"; \
	else \
		python3 -m venv .venv; \
	fi

install: # ignore already installed libraries
	echo "Installing libraries"
	pip3 install -r requirements.txt --exists-action=i -q
	pip3 install git+https://github.com/Omelug/dorkScanner.git#egg=dork_scanner --exists-action=i -q
	pip3 install git+https://github.com/Omelug/python_mini_modules.git#egg=input_parser --exists-action=i -q

install_external_tools:
	/extemkdir -p .rnal_tools
	sudo apt install wpscan
	git clone https://github.com/opsdisk/pagodo.git ./external_tools/pagodo
	cd ./external_tools/pagodo && pip install -r requirements.txt

download_default_wordlists:
	echo "Creating default directories"
	mkdir -p ./wordlists/{wp_link,dorks,pass,user,cewl}
	mkdir -p ./output/{wpscan,pass,user,wpscan_brutal,cracked}

	echo "Downloading default wordlists"
	#Dorks
	if [ ! -f ./wordlists/dorks/google-dorks-for-wordpress.txt ]; then \
 		cd ./wordlists/dorks && wget -nc "https://raw.githubusercontent.com/Proviesec/google-dorks/main/cms/google-dorks-for-wordpress.txt"; \
 	else \
   		echo "Wordlists are downloaded"; \
 	fi

quick_start:
	make venv_init
	make install
	make download_default_wordlists

test:
	python3 -m unittest discover -s tests -p "*_test.py"

#------------FOR DEBUGGING -------------------
venv_clean:
	rm  -rf .venv

req_save:
	pip3 freeze > requirements.txt