#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import logging
import glob, re, socket, time, datetime, subprocess
#from common.sendmail import sendmail
import common.sendmail

logging.basicConfig(level=logging.DEBUG, 
					format='[%(asctime)s][%(levelname)s] %(message)s')

def confirm_host():
	# hostname 확인	
	hostname = socket.gethostname()
	return hostname

def is_pid_same(svcname, basedir):
	# 서비스 상태 확인 (자기자신)
	pid_files = glob.glob(basedir+'/pid*/*'+svcname+'.pid')

	f = open(''.join(pid_files[0]) ,'r')
	pid = f.read().split()

	if os.path.isdir('/proc/'+''.join(pid)+'/') == True:
		return True
	else: 
		return False

def is_open_port(hostname, svcport):
#def is_open_port(svcname, hostname, svcport):
	# 서비스 포트 확인
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.settimeout(10)
	try:
		sock.connect( (hostname, svcport) )
		return True
		sock.close
	except:
		return False
		sock.close

#def tail_trace_log(basedir):
def tail_trace_log(errfile):
	# 서비스 trace로그 last timestatmp확인
	logfile = errfile
	# logfile 에서 gc관련 로그만 제거 하고, 
	# 아래의 os.stat으로 해당 로그만 조회 	
	(mode, ino, dev, nlink, uid, gid, size, 
			atime, mtime, ctime) = os.stat(logfile)
	current_time = int(round(time.time()))	
	
	default_time_gap = 180

	if current_time - mtime <= default_time_gap:
		return True
	else:
		return False

def make_err_file(errfile, svcname, err, msg):
	# 상태가 문제 있을 경우 에러 파일 생성
	datetime.date.fromtimestamp(time.time())
	
	logging.info("%s is %s - %s" % (svcname, err, msg))
	line = '''%s %s \n''' % (
			datetime.datetime.isoformat(
			datetime.datetime.now()), msg)
	
	f = open(errfile, 'a')
	f.write(line)
	f.close

def rsync_err_file(errdir, syncdir):
	# 생성된 에러 파일 rsync
	cmd = ['rsync', '-az', errdir, syncdir ]
	subprocess.call(cmd, shell=False)  

def send_mail(title, send, recv, errfile):
	# 메일 전송
	logging.info("mail success %s" % errfile) 
	f = open(errfile, 'r')
	msg = f.read().replace('\n','\r\n')
	f.close()
	args = ['-s',title, '-f',send, '-r',recv, '-m',msg]
	print(args)
	common.sendmail.sendmail(args)
