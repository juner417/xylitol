#!/usr/bin/python
# -*- coding:utf-8 -*-
import os, sys
import logging, time, re
import subprocess, socket
import common.common
import server
"""
Desctription
1. excludefile을 읽어서 exclude할 노드 확인
2. 순차적으로 한개씩 노드를 hdfs-exclude-host 파일에 쓰고 hadoop dfsadmin -refreshNodes로 exclude 시도
3. exclude 상태를 확인하여 상태가 완료되면 시스템운영팀 프로시져 호출, 아니면 대기
4. 프로시져 호출되고 시스템 재시작 하면 상태 확인 후 재실행
5. 재실행 된 datanode 정상상태 확인 후 반복

file indent = tab(4)
"""

logging.basicConfig(level=logging.DEBUG, 
                    format='[%(asctime)s][%(levelname)s] %(message)s')
ini_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exclude.ini')

if __name__=='__main__':

    exclude_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exclude_node')
    # exclude 대상 파일을 읽어서 제거될 노드 확인    
    f = open(exclude_file, 'r')
    lines = f.readlines()

    for line in lines:
        # 제거될 노드에서 서비스 목록 split
        line_tmp = line.split('\n')[0]
        svr = line_tmp.split(':')[0]
        svcs = line_tmp.split(':')[1].split(',')
        exclude_conf_file = common.common.getconf(ini_file, 'hadoop', 'exclude_conf_file')
        hadoop_home = common.common.getconf(ini_file, 'hadoop', 'hadoop_home')

        logging.info('add node in exclude config file(%s) -  %s' % (exclude_conf_file, svr))

        try:
            # hdfs-exclude 파일에 제거 노드 추가 
            ef = open(exclude_conf_file, 'w')
            ef.write(svr)
            ef.close()
    
        except Exception as e:
            logging.exception('Exception in user code:')

        cmd = [hadoop_home+'/bin/hadoop', 'dfsadmin', '-refreshNodes']
        # refresh node 실행
        logging.info('HDFS dfsadmin Refresh Nodes, Now Decommissioning Nodes %s' % svr)
        subprocess.call(cmd, shell=False)

        decommissing_flag = 1
        while decommissing_flag == 1:
            # decommissing 상태 확인
            is_decommissing = server.check_decommissing(svr, port)
            logging.info('[%s] Currents status - decommissing %s' % (svr, is_decommissing))

            if is_decommissing == False:
                decommissing_flag = 0 
                logging.info('[%s] decommissing is stop, after 15s SERVER RESTART' % svr)
                time.sleep(15)
            else: 
                logging.info('[%s] decommissing is now processing, after 2m re check!' % svr)
                time.sleep(120)

        logging.info('[%s] Now start system procedure' % svr)
        # 시스템 운영팀에서 프로시져 만들어 주면 추가, os 재실행
        # 시스템운영팀 프로시져가 python으로 만들어졌고, sudo 계정으로 실행해야 함... 별도의 방법 생각해야 함
        server.run_procedure(svr, '/home/bigfile')
        time.sleep(120)

        restart_flag = 1
        while restart_flag == 1:
            # 프로시져 실행 후 os 재실행 상태 확인
            is_uptime = server.getuptime(svr)
            
            if is_uptime <= 10800:
                restart_flag = 0
                logging.info('[%s] server restart is done, You should run install script' % svr)
                sender = common.common.getconf(ini_file, 'info', 'mail_sender')
                recv = common.common.getconf(ini_file, 'info', 'mail_reciever')
                mail_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mail', 'mail-'+svr)
                server.make_mail_file(mail_file, svr, 'server restart is done', 'Plz run install script')
                server.send_mail('[INFO] ' +svr+' restart done', sender, recv, mail_file )
                time.sleep(30)
            else:
                logging.info('[%s] server restart is now processing, after 1min re check!!' % svr) 
                time.sleep(60)

        os_set_flag = 1
        while os_set_flag == 1:
            is_restart_done = server.is_open_port(svr, 22)
            
            if is_restart_done == True:
                addscript = 'install.sh'
                status_file = common.common.getconf(ini_file, 'info', 'restart_file_path')              
                server.run_additional_job(svr, addscript)
                
                # status 파일 있으면 작업중-0, 없으면 작업완료-1
                # 그런데 이제 configure_flag가 1이상(작업중일 경우) 계속 run_additional_job을 실행함...
                # addscript에서 status_file이 있을 경우와, addscript가 실행되고 있으면 또 실행하지 말게 설계함 
                list_cmd = [ 'rsh', 'acc@'+svr, 'ls', status_file ]
                p = subprocess.Popen(list_cmd, shell=False, stdout=subprcess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                configure_flag = p.returncode()
                time.sleep(30)
                
                if configure_flag == 0:
                    os_set_flag = 0
                    logging.info('[%s] server OS Setting is done, after 30s next parse' % svr)
                else:
                    logging.info('[%s] server OS Setting is now processing, after 1min re check!! %s' % svr, err)
                    time.sleep(60)
                    
            else:
                logging.error('[%s] server is not running. Plz check ther server. after 30s retry' % svr)
                time.sleep(30)
