#!/bin/bash

CURDIR="${BASH_SOURCE[0]}";RL="readlink";([[ `uname -s`=='Darwin' ]] || RL="$RL -f")
while([ -h "${CURDIR}" ]) do CURDIR=`$RL "${CURDIR}"`; done
N="/dev/null";pushd .>$N;cd `dirname ${CURDIR}`>$N;CURDIR=`pwd`;popd>$N

# This script is preserved for 2.0-compatiblity only and will be removed in the future.
# Use make install directly instead of it.
make -f $CURDIR/Makefile
