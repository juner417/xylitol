#!/usr/bin/python
# -*- coding:utf-8 -*-
import os, sys
import logging, time, re
import subprocess, socket
import common.common, common.sms
import server
"""
Desctription
1. exclude_file(exclude_node)을 읽어서 exclude할 노드랑 서비스 확인
2. 순차적으로 한개씩 노드를 hdfs-exclude-host 파일에 쓰고 hadoop dfsadmin -refreshNodes로 exclude 시도
3. exclude 상태를 확인하여 상태가 완료되면 os upgrade 프로시져 호출, 아니면 대기
4. 프로시져 호출되고 시스템 재시작 하면 상태 확인 후, server init_process 실행
5. 서버 초기 세팅이 완료되면 재실행 된 datanode 정상상태 확인 후 서비스 실행

file indent = tab(4)
"""

logging.basicConfig(level=logging.DEBUG, 
                    format='[%(asctime)s][%(levelname)s] %(message)s')
ini_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exclude.ini')

if __name__=='__main__':

    exclude_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exclude_node')
    # exclude_file(exclude_node) 대상 파일을 읽어서 제거될 노드 확인    
    f = open(exclude_file, 'r')
    lines = f.readlines()

    for line in lines:
        # 제거될 노드에서 서비스 목록 split
        line_tmp = line.split('\n')[0]
        svr = line_tmp.split(':')[0]
        svcs = line_tmp.split(':')[1].split(',')
        exclude_conf_file = common.common.getconf(ini_file, 'hadoop', 'exclude_conf_file')
        hadoop_home = common.common.getconf(ini_file, 'hadoop', 'hadoop_home')

        lf = open(exclude_conf_file, 'r')
        org_exclude_list = lf.read().split('\n')
        if svr in org_exclude_list:
            logging.info('%s already exist in %s, the server is decommissing or done' % 
						(svr, exclude_conf_file))
            sys.exit(1)

        logging.info('add node in exclude config file(%s) -  %s' % (exclude_conf_file, svr))

        try:
            # hdfs-exclude 파일에 제거 노드 추가 
            ef = open(exclude_conf_file, 'a')
            ef.write(svr+'\n')
            ef.close()
    
        except Exception as e:
            logging.exception('Exception in user code:')

        # refresh node 실행
        cmd = [hadoop_home+'/bin/hadoop', 'dfsadmin', '-refreshNodes']
        logging.info('HDFS dfsadmin Refresh Nodes, Now Decommissioning Nodes %s' % svr)
        subprocess.call(cmd, shell=False)

        # decommissing 실행 구문
        decommissing_flag = 1
        while decommissing_flag == 1:
            # decommissing 상태 확인
            is_decommissing = server.check_decommissing(svr, 'your hdfs datanode port') # hdfs datanode port
            logging.info('[%s] Currents status - decommissing %s' % (svr, is_decommissing))

            if is_decommissing == False:
                decommissing_flag = 0 
                logging.info('[%s] decommissing is stop, after 15s SERVER RESTART' % svr)
                time.sleep(15)
            else: 
                logging.info('[%s] decommissing is now processing, after 5min re check!' % svr)
                time.sleep(300)

        logging.info('[%s] Now start system procedure' % svr)
         
        # 프로시져가 python으로 만들어졌고, sudo 계정으로 실행해야 함... 
        remote_lib = common.common.getconf(ini_file, 'info', 'lib_dir')
        os_set_acc = common.common.getconf(ini_file, 'info', 'os_set_acc')
        script = common.common.getconf(ini_file, 'info', 'os_set_script').split(',')
        passwd = common.common.getconf(ini_file, 'info', 'os_set_acc_passwd')
        server.rcp_lib(svr, os_set_acc, passwd, remote_lib)
        server.run_procedure(svr, os_set_acc, 'sudo', passwd,  remote_lib, script[0], '', 30)
        time.sleep(1200) #프로시져 실행 예상 시간 20분 
        
        script.pop(0) #첫 번째 스크립트 사용 후 배열에서 제거
        known_hosts = common.common.getconf(ini_file, 'info', 'known_host_path')
        os.remove(known_hosts) #로컬에 있는 known_host 파일 제거
        tmp_var = 1

        restart_flag = 1
        while restart_flag == 1:
            # 프로시져 실행 후 os 재실행 상태 확인
            logging.info('[%s] uptime check iteration %s' % (svr, tmp_var))
            is_uptime = server.get_uptime(svr)
            
            if is_uptime <= 10800: # os가 재 실행 됬으므로 uptime이 작음
                restart_flag = 0
                logging.info('[%s] server restart is done, You should run install script' % svr)
                # os 설정이 완료 되었으므로 mail alert
                sender = common.common.getconf(ini_file, 'info', 'mail_sender')
                recv = common.common.getconf(ini_file, 'info', 'mail_reciever')
                mail_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mail', 'mail-'+svr)
                server.make_mail_file(mail_file, svr, 'server restart is done', 
										'Now binary sync & svc start')
                server.send_mail('[INFO] ' +svr+' restart done', sender, recv, mail_file )
                time.sleep(15)
            else:
                logging.info('[%s] server restart is now processing, after 1min re check!! - uptime %s' 
                            % (svr, is_uptime)) 
                tmp_var = tmp_var +1
                time.sleep(60)

        # os설정 이후 필요한 필수 패키지 및 서비스 공통 설정 스크립트 실행
        os_set_flag = 1
        while os_set_flag == 1:
            is_restart_done = server.is_open_port(svr, 22)
            
            if is_restart_done == True:
                server.rcp_lib(svr, os_set_acc, passwd, remote_lib)
                time.sleep(30)
                configure_flag = server.run_procedure(svr, os_set_acc, 'sudo', passwd, remote_lib, 
                                                    script[0], '', 100) 
                time.sleep(30)
                
                if configure_flag == True:
                    os_set_flag = 0
                    logging.info('[%s] server OS Setting is done, after 30s next step' % svr)
                else:
                    logging.info('[%s] server OS Setting is now processing, after 1min re check!! %s' % 
								(svr, err))
                    time.sleep(60)
                    
            else:
                logging.error('[%s] server is not running. Plz check ther server. after 30s retry' % svr)
                time.sleep(30)
        # 서비스 binary sync 
        sync_host = common.common.getconf(ini_file, 'info', 'sync_host')
        sync_acc = common.common.getconf(ini_file, 'info', 'sync_acc')
        sync_script = common.common.getconf(ini_file, 'info', 'sync_script')
        sync_acc_passwd = common.common.getconf(ini_file, 'info', 'sync_acc_passwd')

        logging.info('[%s] binary sync %s -> %s' % (svr, sync_host ,svr))
        server.rcp_lib(sync_host, sync_acc, passwd, remote_lib) 
        sync_res = server.run_procedure(sync_host, sync_acc, 'normal' , sync_acc_passwd, remote_lib, 
                                        sync_script, svr, 60)

        # exclude_conf_file($HADOOP_HOME/conf/hdfs-host-exclude) 파일에서 작업완료된 서버 ip제거
        df = open(exclude_conf_file, 'r')
        lines = f.readlines()
        df.close()

        df = open(exclude_conf_file, 'w')
        for line in lines:
            if line != svr + '\n':
                df.write(line + '\n')
        df.close()

        # refresh node 실행
        cmd = [hadoop_home+'/bin/hadoop', 'dfsadmin', '-refreshNodes']
        logging.info('HDFS dfsadmin Refresh Nodes, Now Decommissioning DONE %s' % svr)
        subprocess.call(cmd, shell=False)
        time.sleep(5)
   
        # send sms  
        if sync_res is True:
            logging.info('[%s] hadoop bin sync success, send sms' % svr)
            sms_msg = '''[os]%s-bin sync done''' %svr
        else:
            logging.error('[%s] hadoop bin sync fail, send sms' % svr)
            sms_msg = '''[os-error]%s-bin sync fail''' %svr

        sms_sender = common.common.getconf(ini_file, 'info', 'sms_sender')
        sms_reciever = common.common.getconf(ini_file, 'info', 'sms_reciever')
        logging.info('[%s] all process is done. Plz start hadoop daemons' % svr)
        common.sms.send('default', sms_msg, sms_reciever, sms_sender) 

        # 서비스실행 스크립트 실행 - hdfs mapred ganglia kafka 등 실행
        for svc in svcs:
            svc_acc = common.common.getconf(ini_file, 'svc', svc+'_acc')
            svc_acc_passwd = common.common.getconf(ini_file, 'svc', svc+'_acc_passwd')
            svc_script= common.common.getconf(ini_file, 'svc', 'svc_script')
            svc_timeout = 30
            
            logging.info('[%s] svc start %s script %s' % (svr, svc, svc_script)) 
            svc_res = server.run_procedure(svr, svc_acc, 'normal', svc_acc_passwd, remote_lib, svc_script, 
                                            ' ', svc_timeout) 
