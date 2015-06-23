#!/bin/bash

BIN_HOME=`dirname $0`
SHELL_HOME=`cd ${BIN_HOME}/../; pwd`
USER=`id -un`
SYNC_PATH=""
CMD="rsync -avz"
RECV="phone number"

function print_log() {

    contents=$@
    echo "[`date '+%Y-%m-%d %H:%M:%S'`][$$] ${contents}"
}

function chk_mtime() {
    path=$1

    if [ -f ${path}/.filemtime ]; then 
        print_log "[INFO] file mtime meta file exist"   
    else
        print_log "[INFO] file mtime meta file not exist"
        ls -l --time-style long-iso ${path}/*.err | awk '{print "1970-01-01 00:00",$8}' > ${path}/.filemtime
    fi
    
    for file in `ls ${path}/*.err`; do 
        org_meta_mtime=`cat ${path}/.filemtime | grep ${file} | awk '{print $1,"-",$2}' | tr -d ' '`
        new_file_mtime=`ls -l --time-style long-iso ${file} | awk '{print $6,"-",$7}' | tr -d ' '`

        if [ -z ${org_meta_mtime} ]; then
            print_log "[INFO] ${file} is new sync file, update .filemtime"
            ls -l --time-style long-iso ${file} | awk '{print $6,$7,$8}' >> ${path}/.filemtime

        elif [ ${org_meta_mtime} == ${new_file_mtime} ]; then
            print_log "[INFO] ${file} is not modified,(${org_meta_mtime} -> ${new_file_mtime}) mv backup dir"
            mv ${file} ${path}/backup/ 

        else
            print_log "[INFO] ${file} is modified, .filemtime file change ${org_meta_mtime} -> ${new_file_mtime}"
            cat ${path}/.filemtime | grep -v ${file} > ${path}/.filemtime.tmp
            ls -l --time-style long-iso ${file} | awk '{print $6,$7,$8}' >> ${path}/.filemtime.tmp
            mv ${path}/.filemtime.tmp ${path}/.filemtime
        fi
    done
}

print_log "[INFO] sync start - ${CMD} ${SYNC_PATH}/ ${SHELL_HOME}/"
${CMD} ${SYNC_PATH}/ ${SHELL_HOME}/data/
    
chk_mtime "${SHELL_HOME}/data"

print_log "[INFO] check the err file"

err_files=`ls ${SHELL_HOME}/data/*.err 2> /dev/null`
err_files_cnt=`ls ${SHELL_HOME}/data/*.err 2> /dev/null | wc -l`

if [ ${err_files_cnt} -gt 0 ]; then
    print_log "[WARN] There are ${err_files_cnt} err file"
    cat ${err_files} | awk '{print $2,$3}' | tr -d '[' | tr ']' ' '| awk '{print $1}' | uniq -c > ${SHELL_HOME}/data/sms.res 2>&1
    cat ${SHELL_HOME}/data/sms.res | awk '{print $2,":",$1}' | tr '\n' ' ' | xargs -i echo "Error is occur {}" | xargs -i ${SHELL_HOME}/bin/sms.py "{}" ${RECV}

else
    print_log "[INFO] There are no New err file"
fi
 
