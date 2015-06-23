#!/bin/bash


function configparser() {

    conf_file=$1
    col=$2
    val=( $( awk -v content=$col -F "=" '{if($1==content) print $2}' $conf_file ) )
    echo ${val[@]}
}

function sendmail() {
    sub=$1
    file=$2
    send=$3
    recv=$4
    att=$5

    cat ${file} | ${HOME}/commons/sendmail.py -v smtp -s "${sub}" -f ${send} -r ${recv} -a ${att} -t "html"
}

function print_log() {
    
    contents=$@
    echo "[`date '+%Y-%m-%d %H:%M:%S'`][$$] ${contents}"
}

function createmail() {
    
    logfile=$1
    flag=$2
    
    if [ ${flag} == "pre" ]; then 
	echo "<html>" > ${logfile} 2>&1
	echo "<head>" >> ${logfile} 2>&1
	echo "<style type='text/css'>" >> ${logfile} 2>&1
	echo "table {border-collapse:collapse;margin-top:10px;}" >> ${logfile} 2>&1
	echo "td {font-size:9pt;border:1px solid black;margin:1px 5px 1px 5px;}" >> ${logfile} 2>&1
	echo ".title {font-size:11pt;font-weight:bold;font-color:#DDDDDD;}" >> ${logfile} 2>&1
	echo ".hdr {text-align:center;background-color:#DDDDDD;}" >> ${logfile} 2>&1
	echo ".al {text-align:left;}" >> ${logfile} 2>&1
	echo ".ac {text-align:center;}" >> ${logfile} 2>&1
	echo ".ar {text-align:right;}" >> ${logfile} 2>&1
	echo ".key {font-size:9pt;font-weight:bold;}" >> ${logfile} 2>&1
	echo ".unit {font-size:9pt;}" >> ${logfile} 2>&1
	echo "</style>" >> ${logfile} 2>&1
	echo "</head>" >> ${logfile} 2>&1
	echo "<body>" >> ${logfile} 2>&1
	echo "" >> ${logfile} 2>&1
    else
	echo "</body>" >> ${logfile} 2>&1
	echo "</html>" >> ${logfile} 2>&1 
    fi
}
