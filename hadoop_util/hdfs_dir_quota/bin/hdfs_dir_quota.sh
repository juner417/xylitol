#!/bin/bash

BIN_HOME=`dirname $0`
SHELL_HOME=`cd ${BIN_HOME}/../; pwd`
USER=`id -un`
source ${BIN_HOME}/common/common.sh
CONF="${SHELL_HOME}/conf"
ELEMENTS=( "total" "processing" "user" )
HADOOP_HOME=$( configparser ${CONF}/conf.ini "hadoop_home" )
HIVE_HOME=$( configparser ${CONF}/conf.ini "hive_home" ) 
RESULT=${SHELL_HOME}/data
DT=`date +%Y-%m-%d-%H`

function dir_sum() {

    dir_list=( $( echo $1 ) )
    tbl="hdfs_meta.hdfs_dir_size"
    dt_yyyymmdd=`date +%Y%m%d`
    dt_hhmm=`date +"%Y-%m-%d %H:%M"`
    dt_yyyymm=${dt_yyyymmdd:0:6}
    sql="SET mapred.job.queue.name=QUE1; \
         select log_date, path, spaceconsumed from ${tbl} \
         where path in ( ${dir_list[@]} ) \
         and plogmonth=\"${dt_yyyymm}\" \
         and log_date=\"${dt_yyyymmdd}\" \
         and check_time like \"${dt_hhmm:0:15}0:%\"; "

    ${HIVE_HOME}/bin/hive -e "${sql}"

}

function measure_quota() {

    col=$1
    quota_per=$2
    size_per=$3
    
    if (( $(echo "${size_per} > ${quota_per}" | bc -l) )); then
	flag=1 
    else
	flag=0 
    fi

    echo ${flag}
} 

for e in ${ELEMENTS[@]}; do 
   
    dirs=( $( configparser ${CONF}/conf.ini ${e}_dir ) )
    print_log "[INFO] ${e} dir(${dirs[@]}) size are now quering" 
    
    dir_sum "${dirs[@]}" > ${RESULT}/${e}_hive.res 2> ${RESULT}/${e}_hive.log
    
    current_size=`cat ${RESULT}/${e}_hive.res | awk 'BEGIN{SUM} {SUM+=$3} END{print SUM}'`
    quota_per=$( configparser ${CONF}/conf.ini ${e} )
    
    if [ $e == "total" ]; then 
        limit_size=$( configparser ${CONF}/conf.ini "hdfs_total_capacity" )
    else
        limit_size=$( configparser ${CONF}/conf.ini "hdfs_limit_capacity" ) 
    fi
        
    print_log "[INFO] ${e} dir(${dirs[@]}) size compare with the qouta" 

    current_per=$( echo "scale=2; ${current_size} / ${limit_size} * 100" | bc -l )
    flag=$( measure_quota "${e}" ${quota_per} ${current_per} )

    if [ ${flag} -eq 1 ]; then 
        print_log "[WARN] ${e} hdfs size greater than qouta ${current_per} : ${quota_per}"

        sendfile="$e-alert-mail-`date +%Y%m%d`.log"
        quota_usage_tmp=$( echo "scale=2; ${quota_per} / 100" | bc -l )
        quota_usage=$( echo "scale=0; ${quota_usage_tmp} * ${limit_size}" | bc -l )
        size_diff=$( echo "scale=0; ${current_size} - ${quota_usage}" | bc -l )
        size_diff_gb=$( echo "scale=0; ${size_diff}/1024/1024/1024" | bc -l )

        createmail "${RESULT}/${sendfile}" "pre" 

        echo "<table><tr><td colspan=2 style='border:0px;vertical-align:top;'>" >> ${RESULT}/${sendfile}
        echo "<span class='title'>${e} HDFS quota limit excess</span></br>" >> ${RESULT}/${sendfile}
        echo "</td></tr>" >> ${RESULT}/${sendfile}
        echo "<tr><td style='border:0px;vertical-align:top;'>" >> ${RESULT}/${sendfile}
        echo "<table width="430" style="table-layout:fixed">" >> ${RESULT}/${sendfile}
        echo "<tr><td class='hdr'>${e} dir</td><td class='ar'>${dirs[@]}</td></tr>" >> ${RESULT}/${sendfile}
        echo "<tr><td class='hdr'>current size/percent</td><td class='ar'>${current_size} / ${current_per} %</td></tr>" >> ${RESULT}/${sendfile}
        echo "<tr><td class='hdr'>limit quota size/percent</td><td class='ar'>${quota_usage} / ${quota_per} %</td></tr>" >> ${RESULT}/${sendfile}
        echo "<tr><td class='hdr'>excess size</td><td class='ar'>${size_diff}</td></tr>" >> ${RESULT}/${sendfile}
        echo "<tr><td colspan=2>${e} 디렉토리가 할당된 사이즈 보다 ${size_diff_gb}GB만큼 넘었습니다.<br>디렉토리 공간 확보 부탁드립니다.</br></td></tr>" >> ${RESULT}/${sendfile}
        echo "</table>" >> ${RESULT}/${sendfile}
        echo "</td><td style='border:0px;vertical-align:bottom;'>" >> ${RESULT}/${sendfile}
        echo "</td></tr></table></br>" >> ${RESULT}/${sendfile}

        createmail "${RESULT}/${sendfile}" "post"

        attach=${RESULT}/${e}_hive.res
        sender=$( configparser ${CONF}/conf.ini sender )
        reciver=$( configparser ${CONF}/conf.ini ${e}_reciver )

        sendmail "[REPORT][Alert] HDFS Quota Limit Alert(dirs : ${e}, DT : ${DT})" "${RESULT}/${sendfile}" "${sender}" "${reciver}" "${attach}"
    else
        print_log "[INFO] It's OK ${e} hdfs size(${current_size}) less than qouta, current ${current_per} : ${quota_per} %"
    fi
done

