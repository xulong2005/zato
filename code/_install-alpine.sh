#!/bin/sh -e

CURDIR=`readlink -f .`

symlink_py() {
  target=`python -c 'import '${1}', os.path, sys; sys.stdout.write(os.path.dirname('${1}'.__file__))'`
  rm -f "$CURDIR/zato_extra_paths/$1"
  ln -s "$target" "$CURDIR/zato_extra_paths/$1"
}

$CURDIR/clean.sh


# We only need to do the following if we're being run from a
# manual install.sh invocation. If we're running from abuild,
# then build-zato.sh or abuild is already taking care of all this for us.

if test -z "$RUNNING_FROM_ABUILD" ; then

# Always run an update so there are no surprises later on when it actually
# comes to fetching the packages from repositories.

if test -z "$PREFERRED_REPOSITORY" ; then
  PREFERRED_REPOSITORY=http://dl-5.alpinelinux.org/alpine
fi

if test -z "$ALPINE_FLAVOUR" ; then
  ALPINE_FLAVOUR=v3.6
fi

  sudo apk update

  sudo apk add py-numpy py-numpy-f2py --update-cache --repository "$PREFERRED_REPOSITORY/$ALPINE_FLAVOUR/community"
  sudo apk add py-scipy --update-cache --repository "$PREFERRED_REPOSITORY/edge/testing"
  sudo apk add gcc g++ git gfortran haproxy libbz2 libev libev-dev libevent libevent-dev \
    libgfortran libffi-dev libldap libpq libsasl libuuid libxml2-dev libxslt-dev \
    linux-headers musl-dev openldap-dev openssl postgresql-dev py2-pip python2-dev swig yaml-dev
fi


# Work around an inconsistency in the way Alpine installs zlib
if test -f /usr/lib/libz.so ; then
  :
else
  sudo ln -s ../../lib/libz.so /usr/lib/libz.so
fi

mkdir -p $CURDIR/zato_extra_paths

symlink_py numpy
symlink_py scipy

CYTHON=$CURDIR/bin/cython
export CYTHON

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
