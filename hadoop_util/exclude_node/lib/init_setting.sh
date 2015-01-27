#!/bin/bash

# init_setting.sh
# os upgrade가 완료된 서버에 보내져 기본 setting을 진행함

# main

(
    # flock -w: timeout 20sec, -n: 바로 lock을 얻을수 없을경우 대기 하기 보다는 fail
    # 200은 fd
    flock -n -w 20 200

    if [ "$?" != "0" ]; then
        echo "locked"
        exit 1
    fi
    
    # setting script
    
    echo "done"
) 200> /var/lock/.init_setting.exclusivelock
