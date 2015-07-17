#!/usr/bin/python
#-*- coding: utf-8 -*-
# fail recognizer
# file indent 4 space
import os, sys
import socket, subprocess, MySQLdb, logging

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s][%(levelname)s] %(message)s')

def is_port_open(hostname, port):
    # 서비스 포트 확인
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    try:
        sock.connect((hostname, port))
        return True
        sock.close
    except: 
        return False
        sock.close

def is_pid_exist(hostname, pid_file):
    # 서비스 pid 파일 확인 
    ssh = subprocess.Popen(['ssh', hostname, 'cat %s' % pid_file ], 
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        
    pid = ssh.stdout.readline().strip('\n')
    # pid 확인했으면 그 pid로 프로세스 확인
    #if isinstance(pid, int):
    if pid != "":
        pid_dir = subprocess.Popen(['ssh', hostname, '[ -d /proc/%s ] && echo $?' % pid], 
                                   shell=False,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        pid_exist = pid_dir.stdout.readline().strip('\n')
        logging.info('[%s] pid : %s, process exist! ' % (hostname, pid))
    else: 
        pid = 0
        logging.error('[%s] server has not pidfile: %s ' % (hostname, pid))

    return int(pid)

def search_db(hostname, dbuser, passwd, dbport, dbname, sql):
    # db 조회
    try: 
        db = MySQLdb.connect(host=hostname, port=dbport, user=dbuser, 
                             passwd=passwd, db=dbname)
        cur = db.cursor()
        cur.execute(sql)
        res = []
        for row in cur.fetchall():
            res.append(row)
   
        db.close()
    except IOError as e:
        res = None

    return res

def search_dummy(hostname):
    # dummy 조회
    print(hostname)

# test main
if __name__=='__main__':

    sql = '''
    '''
    res = 
    for i in res:
        print('%s  %s %s' %(i[0], i[1], i[2]))

    res = 
    print(res)
    res1 = 
    for line in res1:
        print('res: %s - exist' % (line))

