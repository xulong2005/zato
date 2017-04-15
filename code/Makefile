
.PHONY: install

ENV_NAME=env-zato
BIN_DIR=$(CURDIR)/$(ENV_NAME)/bin

IS_DEB=$(shell apt-get -h > /dev/null 2>&1; echo $$?)
IS_RHEL=$(shell yum --help > /dev/null 2>&1; echo $$?)

##################################################################################################################################

install:

	$(MAKE) clean

# There cannot be leading whitespace in these ifeq blocks:
# https://stackoverflow.com/questions/21226905/syntax-error-word-unexpected-expecting

ifeq ($(IS_DEB), 0)
	$(MAKE) deb-install
else ifeq ($(IS_RHEL), 0)
	$(MAKE) rhel-install
endif

##################################################################################################################################

deb-install:

	# DEB-specific packages and dependencies
	sudo apt-get update
	sudo apt-get install -y git bzr gfortran haproxy \
		libatlas-dev libatlas3-base libblas3 \
		libbz2-dev libev4 libev-dev \
		libevent-dev libgfortran3 liblapack-dev liblapack3 libldap2-dev \
		libpq-dev libsasl2-dev libyaml-dev libxml2-dev libxslt1-dev \
		libumfpack* make openssl python2.7-dev python-numpy python-pip \
		swig uuid-dev uuid-runtime libffi-dev libssl-dev

	# So that the 'zato' user can run HAProxy straight from its $PATH
	sudo ln -sf /usr/sbin/haproxy /usr/bin/haproxy

	# Common installation path
	$(MAKE) _common-install

##################################################################################################################################

rhel-install:

	# RHEL-specific packages and dependencies
	sudo yum update
	sudo yum -y install git bzr gcc-gfortran haproxy \
		gcc-c++ atlas-devel atlas blas-devel  \
		bzip2 bzip2-devel cyrus-sasl-devel libev libev-devel libffi libffi-devel \
		libevent-devel libgfortran lapack-devel lapack \
		libpqxx-devel libyaml-devel libxml2-devel libxslt-devel suitesparse \
		openssl openssl-devel python-devel python-pip \
		swig uuid-devel uuid

	# Common installation path
	$(MAKE) _common-install

##################################################################################################################################

_common-install:

	git log -n 1 --pretty=format:"%H" > $(CURDIR)/release-info/revision.txt
	$(MAKE) pip-venv-install
	$(MAKE) _add-binaries
	$(MAKE) _apply-patches

##################################################################################################################################

pip-venv-install:

	sudo pip install --upgrade pip
	sudo pip install virtualenv==15.1.0
	virtualenv --no-site-packages -p python $(CURDIR)/$(ENV_NAME)

	$(BIN_DIR)/pip install setuptools==34.4.1
	$(BIN_DIR)/pip install cython
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
	$(BIN_DIR)/pip install -r $(CURDIR)/requirements.txt

##################################################################################################################################

_add-binaries:
	. $(BIN_DIR)/activate
	$(BIN_DIR)/python $(CURDIR)/scripts/add-binaries.py $(CURDIR)/bin

##################################################################################################################################

_apply-patches:
	echo "Applying patches"

##################################################################################################################################

clean:
	rm -rf $(CURDIR)/$(ENV_NAME)
	rm -rf $(CURDIR)/bin/*
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
