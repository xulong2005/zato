
.PHONY: test

ENV_NAME=env-zato
BIN_DIR=$(CURDIR)/$(ENV_NAME)/bin

##################################################################################################################################

install-deb:
	sudo pip install --upgrade pip
	sudo pip install virtualenv==15.1.0
	virtualenv --no-site-packages -p python $(CURDIR)/$(ENV_NAME)
	$(MAKE) _install

##################################################################################################################################

_install:
	$(BIN_DIR)/pip install setuptools==34.4.1
	$(BIN_DIR)/pip install Cython
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-agent
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-broker
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-cli
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-client
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-common
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-cy
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-distlock
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-scheduler
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-server
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-web-admin
	$(BIN_DIR)/pip install -e $(CURDIR)/zato-zmq
	$(BIN_DIR)/pip install -r $(CURDIR)/reqs.txt
	$(MAKE) _add_binaries

##################################################################################################################################

_add_binaries:
	. $(BIN_DIR)/activate
	$(BIN_DIR)/python $(CURDIR)/add_binaries.py $(CURDIR)/bin

##################################################################################################################################

clean:
	rm -rf $(CURDIR)/$(ENV_NAME)
	rm -rf $(CURDIR)/build
	rm -rf $(CURDIR)/dist
	rm -rf $(CURDIR)/src/zato_vault_client.egg-info
	find $(CURDIR) -name '*.pyc' -exec rm {} \;

##################################################################################################################################

test:
	$(MAKE) pyflakes

##################################################################################################################################

pyflakes:
	$(BIN_DIR)/pyflakes $(CURDIR)/src
	$(BIN_DIR)/pyflakes $(CURDIR)/test

##################################################################################################################################
