BIN = /usr/local/bin/ebizzle

ifeq ($(shell uname -s),Darwin)
	GROUP = staff
else
	GROUP = $(USER)
endif

create_virtualenv:
	virtualenv env
	env/bin/pip install -r requirements/requirements.txt

create_bin:
	sudo touch $(BIN) && \
		sudo chown $(USER):$(GROUP) $(BIN)
	echo "#!/bin/bash" > $(BIN)
	echo "$(shell pwd)/env/bin/python $(shell pwd)/src/ebizzle.py \$$@" >> $(BIN)
	chmod +x $(BIN)

install: create_virtualenv create_bin

clean:
	rm -rf env
	sudo rm -f $(BIN)
