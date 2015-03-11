BIN = /usr/local/bin/ebizzle

create_virtualenv:
	virtualenv env
	env/bin/pip install -r requirements/requirements.txt

create_bin:
	echo "#!/bin/bash" > $(BIN)
	echo "$(shell pwd)/env/bin/python $(shell pwd)/src/ebizzle.py \$$@" >> $(BIN)
	chmod +x $(BIN)

install: create_virtualenv create_bin

clean:
	rm -rf env
	rm -f $(BIN)
