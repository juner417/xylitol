#!/usr/bin/python
# -*- coding:utf-8 -*-

import os, sys
import socket, subprocess
import datetime, time
import common.sendmail
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s][%(levelname)s] %(message)s')

def is_open_port(hostname, svcport):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect( (hostname, svcport) )
        return True
        sock.close
    except:
        return False
        sock.close

def check_decommissing(hostname, portnum):

    host = hostname
    port = portnum
    flag = is_open_port(host, port)

    if flag == True:
        return True
    else :
        return False

def run_procedure(hostname, proce_home):
    
    cmd = ['rsh', hostname,'sudo', proce_home+'/procfile.sh']
    print(cmd)
    
    #subprocess.call(cmd, shell=False)
    return True

def run_service(server, service):

    print('start %s %s' % (server, service))
    return True

def run_additional_job(server, cmd):

    print('start %s %s' % (server, cmd))
    return True

def get_uptime(server): 
    
    cmd = ['ssh', 'acc@'+server, 'cat /proc/uptime']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()

    if err is not None:
        '''만약 서버가 reboot중일 경우 timeout일 경우 에러가 발생하므로 3시간 보다 큰 uptime을 너어 줘 
           while문을 못 빠지게 함 ''' 
        uptime = 20000
    else:
        uptime = output.split()[0]
    return uptime

def check_server_status():
    # os재설치 된 서버의 상태 확인
    # os(kernel)version, uid(gid), ulimit, hostfile count, sysctl file, jdk version
    print('hello') 

def send_mail(title, send, recv, mailfile):
        # 메일 전송
        logging.info("mail success %s" % mailfile)
        f = open(mailfile, 'r')
        msg = f.read().replace('\n','\r\n')
        f.close()
        args = ['-v', '','-s',title, '-f',send, '-r',recv, '-m',msg]
        print(args)
        common.sendmail.sendmail(args)

def make_mail_file(mailfile, svr, event, msg):
        # 서버 정상으로 올라오면 mail file 생성
        datetime.date.fromtimestamp(time.time())

        logging.info("%s is %s - %s" % (svr, event, msg))
        line = '''%s %s \n''' % (
                        datetime.datetime.isoformat(
                        datetime.datetime.now()), msg)

        f = open(mailfile, 'a')
        f.write(line)
        f.close
