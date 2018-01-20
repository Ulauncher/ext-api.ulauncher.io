#!/bin/bash


cd `dirname $0`
cd ..

PYTHONPATH=`pwd` python ext_api/db/extensions.py
