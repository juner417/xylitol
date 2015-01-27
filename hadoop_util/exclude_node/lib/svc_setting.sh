#!/bin/bash

# file : svc_setting.sh
# service setting.sh

user_id=`id -un`
HADOOP_PATH=''
KAFKA_PATH=''
GANGLIA_PATH=''

if [ ${user_id} == 'hdfs' ];
	cd ${HADOOP_PATH}/bin/ ; ./hadoop-daemon.sh start datanode; cd ${HADOOP_PATH}/logs;
elif [ ${user_id} == 'mapred' ];
	cd ${HADOOP_PATH}/bin/ ; ./hadoop-daemon.sh start tasktracker; cd ${HADOOP_PATH}/logs;
elif [ ${user_id} == 'kafka' ];
	cd ${KAFKA_PATH}
elif [ ${user_id} == 'ganglia' ];
	cd ${GANGLIA_PATH}; ./start-ganglia.sh
	cat << EOF >> CRON
@reboot ${GANGLIA_PATH}/start-ganglia.sh
EOF
	crontab CRON
else 
	echo "${user_id} has not service"
