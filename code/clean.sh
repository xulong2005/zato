#!/bin/sh -e

rm -rf bin develop-eggs downloads eggs include .installed.cfg .coverage lib local parts zato_extra_paths
find . -name \*.pyc -delete 
