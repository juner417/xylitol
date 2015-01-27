#!/usr/bin/python
# -*- coding:utf-8 -*-

import os, sys
import socket, subprocess, pexpect
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

def rcp_lib(hostname, remote_acc, passwd, script_path):
    # library file전송 
    msg = 'Are you sure you want to continue connecting'
    child = pexpect.spawn('rcp -r ' + script_path + '/' + ' ' + remote_acc + '@' 
							+ hostname + ':/tmp/', timeout=60)
    index = child.expect([msg, 'password', pexpect.EOF, pexpect.TIMEOUT])

    #print("%s scp first index:%s " % (script_path, index)) #debug 
    if index == 0:
        child.sendline('yes')
        index = child.pexpect([msg, 'password', pexpect.EOF, pexpect.TIMEOUT])

    if index == 1:
        child.sendline(passwd)
        child.expect(pexpect.EOF)
        return True
    elif index == 2:
        # print('rcp second result %s' % child.before) #debug 
        return True
    else :
        print('cannot connect to %s ' % hostname)
        return False

def run_procedure(hostname, remote_acc, perm, passwd, script_path, script, args, script_timeout):
    # run procedure - pexpect로 수정해야 함..
    msg = 'Are you sure you want to continue connecting'
    if perm == 'sudo':
        cmd_prefix = 'sudo'
    else:
        cmd_prefix = ' '

    if script.split('.')[1] == 'py':
        cmd_prefix = cmd_prefix + ' python'
    
    script_dir = script_path[script_path.rfind('/'):]
    child = pexpect.spawn('rsh ' + remote_acc + '@' + hostname + ' ' + cmd_prefix + ' /tmp' + script_dir 
                        + '/' + script + ' ' + args, timeout=script_timeout)
    index = child.expect([msg, 'password', pexpect.EOF, pexpect.TIMEOUT])
    # print("%s run_proc first index:%s " % (script, index)) #debug

    if index == 0:
        child.sendline('yes')
        index = child.expect([msg, 'password', pexpect.EOF, pexpect.TIMEOUT])

    if index == 1:
        child.sendline(passwd)
        child.expect(pexpect.EOF)
        # print('index1 output : %s' % child.before) #debug
        return True
    elif index == 2:
        print('%s script run result %s' % (script, child.before))
        return True 
    else:
        print('cannot connect to %s and run %s' %(hostname, script))
        return False

def get_uptime(server):

    msg = 'Are you sure you want to continue connecting'
    
    try:
        child = pexpect.spawn('ssh acc@'+server+' cat /proc/uptime')
        index = child.expect([msg, 'password', pexpect.EOF, pexpect.TIMEOUT])
        # print('getuptime 1st index %s' %index) #debug 

        if index == 0:
            child.sendline ('yes')
            index = child.expect([msg, 'password', pexpect.EOF, pexpect.TIMEOUT])

        if index == 1:
            child.sendline('acc_passwd')
            child.expect(pexpect.EOF)
            uptime = float(child.before.split()[0])
            # print('index 1 uptime is : %s' %uptime) #debug 
        elif index == 2:
            print('cannot read server uptime')
            try:
                uptime = float(child.before.split()[0])
                # print('uptime is float : %s' %uptime) #debug 
            except:
                print('except is occur :%s' % child.before)
                # print('uptime is set 50000') #debug 
                uptime = 50000
    except:
        print('uptime spawn except. will retry')
        uptime = 50000

    return uptime

def send_mail(title, send, recv, mailfile):
        # 메일 전송
        logging.info("mail success %s" % mailfile)
        f = open(mailfile, 'r')
        msg = f.read().replace('\n','\r\n')
        f.close()
        args = ['your mail api args ']
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
