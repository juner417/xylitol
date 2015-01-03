#!/bin/bash

# init_setting.sh
# os upgrade가 완료된 서버에 보내져 기본 setting을 진행함
# 1. 계정별 .ssh key 배포(expect 파일 필요)
# 2. /data link 생성
# 3. /data/cluster/ncc1/ 디렉토리 생성 및 권한 부여
# 4. 각 서비스 별 바이너리 sync
# 5. /data??/hdfs, /data??/mapred 디렉토리 생성 및 권한 부여

function print_log() {

	contents=$@
	echo "[`date '%y-%m-%d %T'`][$$] ${contents}"

}
function fsync() {

	src=$1
	desc=$2


}

function create_lock() {
	
	file='/home/acc/status'

}


# main
pid=$$
myself=$0
file_flag=`ps -ef | grep ${myself} | wc -l`
status_file='/home/acc/status'

if [ ${file_flag} -ge 1 ] || [ -f ${status_file} ]; then 
	print_log "[ERROR] another process is running"
	exit()
fi


