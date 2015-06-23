#!/usr/bin/python
# -*-- coding: utf-8 -*-

import os, sys
import logging
import server
import subprocess, socket, glob
import ConfigParser

def getconf(filename, title, value):
	ini_path = filename

	config = ConfigParser.RawConfigParser()
	config.read(ini_path)

	value = config.get(title, value)
	
	return value
	

if __name__=="__main__":

	hostname = socket.gethostname() 
	configfile = os.path.join(os.path.dirname(
						os.path.abspath(__file__)), 
						'../','conf/servers.ini')
	logfile = getconf(configfile, 'basedir', 'log')
	logging.basicConfig(level=logging.DEBUG, 
						format='[%(asctime)s][%(levelname)s] %(message)s')

	error_dir = getconf(configfile, 'errdir', 'errdir')
	sync_dir = getconf(configfile, 'errdir', 'rsyncdir')

	mail_sender = getconf(configfile, 'alert', 'sender')
	mail_reciver = getconf(configfile, 'alert', 'reciver')
	
	## chk the service list
	svc_lists = getconf(configfile, 'service', 'svc')

	for svc_arg in svc_lists.split(","):
		localsvc = getconf(configfile, 'service', svc_arg)

		try: 
			# hostname을 가지고 svc와 basedir 확인
			localsvc.index(hostname) 
		except:
			continue
	
		logging.info('[HOSTNAME] : %s ' % hostname)
		svc = svc_arg
		svc_port = getconf(configfile, 'service', svc_arg+'_port')
		logging.info('[SVC] This server is %s : %s' % (svc, svc_port))

		basedir = getconf(configfile, 'basedir', svc)
		error_file = os.path.join(error_dir,
								  hostname+'-service.err')
		
		#1.svc status 체크 port, pid, tracelog(이 부분은 추가 개발...)
		svc_pids = server.is_pid_same(svc, basedir)	
		svc_status = server.is_open_port(hostname, int(svc_port))
		
		if svc_pids == True & svc_status == True:
			logging.info('[SVC] %s status is well' % svc)	

		else:
			msg = '''[SVC][%s %s] port: %s, svc_status: %s, pid_status: %s''' % (
					svc, hostname, svc_port, svc_status, svc_pids)
			server.make_err_file(error_file, svc, 'fail', msg)

	# check the server alive
	svr_list = getconf(configfile, 'servers', 'cluster')

	for svr in svr_list.split(","):
		if svr == "cluster-windows":
			svr_port = 3389
		else : 
			svr_port = 22
		
		try :
			error_file = os.path.join(error_dir, 
										hostname+'-server.err')
		
			# 1. svr status 체크 port(22)
			svr_status = server.is_open_port(svr, svr_port)

			if svr_status == True: 
				logging.info('[SERVER] %s server is alive' % svr)
			else:
				msg = '''[SERVER][%s] %s server is down''' % (svr, svr)
				server.make_err_file(error_file, svr, 'down', msg)
		except Exception as e:
			logging.exception("Exception in user code:")
			continue

	# check the err file
	# 에러파일 디렉토리 확인
	errfile_list = glob.glob(error_dir+'/*')
	if len(errfile_list) >= 1:
		for err in errfile_list:
			err_flag = server.tail_trace_log(err)
			if err_flag == True:
				logging.info('%s file is modifying and send a email' % err)
				mail_title = '[Alert] %s server error file exists' % hostname
				server.send_mail(mail_title, mail_sender, mail_reciver, err)
				server.rsync_err_file(error_dir, sync_dir)
			else:
				logging.info('%s file is not modified during last 3 min' % err)	
		logging.info('error file sync' % errfile_list)		
		#server.rsync_err_file(error_dir, sync_dir)
