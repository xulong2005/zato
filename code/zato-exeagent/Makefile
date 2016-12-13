
ENV_NAME=exeagent-env
BIN_DIR=$(CURDIR)/$(ENV_NAME)/bin

default: install3

install3:
	virtualenv -p python3 $(CURDIR)/$(ENV_NAME)
	$(MAKE) _install

_install:
	$(BIN_DIR)/pip install -r $(CURDIR)/requirements.txt
	$(BIN_DIR)/python $(CURDIR)/setup.py develop
	$(BIN_DIR)/pip install -e $(CURDIR)/.

clean:
	rm -rf $(CURDIR)/$(ENV_NAME)
	rm -rf $(CURDIR)/build
	rm -rf $(CURDIR)/dist
	rm -rf $(CURDIR)/src/zato_exeagent.egg-info
	find $(CURDIR) -name '*.pyc' -exec rm {} \;

flake8:
	$(BIN_DIR)/flake8 $(CURDIR)/src --count
	$(BIN_DIR)/flake8 $(CURDIR)/test --count
