#!/bin/bash

bin_path=`dirname $0`
path=`cd ${bin_path}/../; pwd`

python ${path}/check.py -s all -m mail,jira
