#!/bin/bash

BIN_HOME=`dirname $0`
SHELL_HOME=`cd ${BIN_HOME}/../; pwd`
USER=`whoami`
DT=`date +%Y%m%d`
LOGS="${SHELL_HOME}/logs"

/usr/bin/python ${BIN_HOME}/start.py 1>> ${LOGS}/process.log.${DT} 2>&1
