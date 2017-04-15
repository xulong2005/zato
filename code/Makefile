
.PHONY: install

ENV_NAME=env-zato
BIN_DIR=$(CURDIR)/$(ENV_NAME)/bin
PATCHES_DIR=$(CURDIR)/patches

# For now, assume we are always on Python 2.7
SITE_PACKAGES=$(CURDIR)/$(ENV_NAME)/lib/python2.7/site-packages

IS_DEB=$(shell apt-get -h > /dev/null 2>&1; echo $$?)
IS_RHEL=$(shell yum --help > /dev/null 2>&1; echo $$?)

PATCH_CMD=patch --forward --input

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

	# Applies patches but ignores errors (leading dash) so that this target can be re-run multiple times
	# if needed. This is handy during development.

	# patch_anyjson
	-$(PATCH_CMD) $(PATCHES_DIR)/anyjson/__init__.py.diff $(SITE_PACKAGES)/anyjson/__init__.py

	# patch_butler
	-$(PATCH_CMD) $(PATCHES_DIR)/butler/__init__.py.diff $(SITE_PACKAGES)/butler/__init__.py

	# patch_gunicorn
	-$(PATCH_CMD) $(PATCHES_DIR)/gunicorn/workers/base.py.diff $(SITE_PACKAGES)/gunicorn/workers/base.py

	# patch_gunicorn_arbiter
	-$(PATCH_CMD) $(PATCHES_DIR)/gunicorn/arbiter.py.diff $(SITE_PACKAGES)/gunicorn/arbiter.py

	# patch_gunicorn_logger
	-$(PATCH_CMD) $(PATCHES_DIR)/gunicorn/glogging.py.diff $(SITE_PACKAGES)/gunicorn/glogging.py

	# patch_gunicorn_tls
	-$(PATCH_CMD) $(PATCHES_DIR)/gunicorn/config.py.diff $(SITE_PACKAGES)/gunicorn/config.py
	-$(PATCH_CMD) $(PATCHES_DIR)/gunicorn/workers/geventlet.py.diff $(SITE_PACKAGES)/gunicorn/workers/geventlet.py
	-$(PATCH_CMD) $(PATCHES_DIR)/gunicorn/workers/ggevent.py.diff $(SITE_PACKAGES)/gunicorn/workers/ggevent.py
	-$(PATCH_CMD) $(PATCHES_DIR)/gunicorn/workers/sync.py.diff $(SITE_PACKAGES)/gunicorn/workers/sync.py

	# patch_hvac
	-$(PATCH_CMD) $(PATCHES_DIR)/hvac/__init__.py.diff $(SITE_PACKAGES)/hvac/__init__.py

	# patch_jsonpointer
	-$(PATCH_CMD) $(PATCHES_DIR)/jsonpointer/jsonpointer.py.diff $(SITE_PACKAGES)/jsonpointer/jsonpointer.py

	# patch_oauth
	-$(PATCH_CMD) $(PATCHES_DIR)/oauth/oauth.py.diff $(SITE_PACKAGES)/oauth/oauth.py

	# patch_outbox
	-$(PATCH_CMD) $(PATCHES_DIR)/outbox/outbox.py.diff $(SITE_PACKAGES)/outbox/outbox.py
	-$(PATCH_CMD) $(PATCHES_DIR)/outbox/outbox.py2.diff $(SITE_PACKAGES)/outbox/outbox.py
	-$(PATCH_CMD) $(PATCHES_DIR)/outbox/outbox.py3.diff $(SITE_PACKAGES)/outbox/outbox.py
	-$(PATCH_CMD) $(PATCHES_DIR)/outbox/outbox.py4.diff $(SITE_PACKAGES)/outbox/outbox.py

	# patch_redis
	-$(PATCH_CMD) $(PATCHES_DIR)/redis/redis/connection.py.diff $(SITE_PACKAGES)/redis/redis/connection.py

	# patch_requests
	-$(PATCH_CMD) $(PATCHES_DIR)/requests/models.py.diff $(SITE_PACKAGES)/requests/models.py
	-$(PATCH_CMD) $(PATCHES_DIR)/requests/sessions.py.diff $(SITE_PACKAGES)/requests/sessions.py
	-$(PATCH_CMD) $(PATCHES_DIR)/requests/packages/urllib3/connectionpool.py.diff $(SITE_PACKAGES)/requests/packages/urllib3/connectionpool.py

	# patch_springpython
	-$(PATCH_CMD) $(PATCHES_DIR)/springpython/jms/factory.py.diff $(SITE_PACKAGES)/springpython/jms/factory.py

	# patch_ws4py
	-$(PATCH_CMD) $(PATCHES_DIR)/ws4py/server/geventserver.py.diff $(SITE_PACKAGES)/ws4py/server/geventserver.py

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
