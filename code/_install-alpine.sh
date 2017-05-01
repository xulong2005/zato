#!/bin/bash

#
# Taken from https://gist.github.com/josephwecker/2884332
#
CURDIR="${BASH_SOURCE[0]}";RL="readlink";([[ `uname -s`=='Darwin' ]] || RL="$RL -f")
while([ -h "${CURDIR}" ]) do CURDIR=`$RL "${CURDIR}"`; done
N="/dev/null";pushd .>$N;cd `dirname ${CURDIR}`>$N;CURDIR=`pwd`;popd>$N

function symlink_py {
    ln -s `python -c 'import '${1}', os.path, sys; sys.stdout.write(os.path.dirname('${1}'.__file__))'` $CURDIR/zato_extra_paths
}

bash $CURDIR/clean.sh

# Always run an update so there are no surprises later on when it actually
# comes to fetching the packages from repositories.
sudo apk update

#
# These are missing:
#
# bzr
# libatlas-dev
# libatlas3-dev
# libblas3
# liblapack
# libumfpack
# python-numpy
# python-scipy

sudo apk add gcc g++ git gfortran haproxy libbz2 libev libev-dev libevent libevent-dev \
    libgfortran libffi-dev libldap libpq libsasl libuuid libxml2-dev libxslt-dev \
    linux-headers musl-dev openldap-dev openssl postgresql-dev py2-pip python2-dev swig yaml-dev

mkdir $CURDIR/zato_extra_paths

export CYTHON=$CURDIR/bin/cython

sudo pip install --upgrade pip
sudo pip install distribute==0.7.3
sudo pip install virtualenv==15.1.0
sudo pip install zato-apitest

virtualenv $CURDIR
$CURDIR/bin/pip install --upgrade pip

$CURDIR/bin/python bootstrap.py -v 1.7.0
$CURDIR/bin/pip install setuptools==31.0.1
$CURDIR/bin/pip install cython==0.22
$CURDIR/bin/buildout

echo
echo OK

