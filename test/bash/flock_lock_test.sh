#!/bin/bash
# flock_lock_test.sh

(
    # flock -w: timeout 20sec, -n: 바로 lock을 얻을수 없을경우 대기 하기 보다는 fail
    # 200은 fd
    flock -n -w 20 200

    if [ "$?" != "0" ]; then
        echo "locked"
        exit 1
    fi
    
    #echo $$ >>/var/lock/.init_setting.exclusivelock

    for i in `seq -f %02g 1 10`; do 
        echo ${i}
        sleep 1
    done
    echo "done"
) 200> /var/lock/.init_setting.exclusivelock

# reference
# http://stackoverflow.com/questions/169964/how-to-prevent-a-script-from-running-simultaneously
