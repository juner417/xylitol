#!/usr/bin/python 
#-*- coding: utf-8 -*-

import os, sys, socket, ConfigParser, time
from lib import *

'''
Description 
    author = juner
    python version = 2.7
    file indent = 4 space
'''

if __name__=='__main__':


    if len(sys.argv) < 2:
        commons.print_usage()
        exit(2)

    file_path = os.path.abspath(__file__)
    config = os.path.join(os.path.dirname(file_path),
                          'conf','fail_detection.ini')

    svcs, mode = commons.read_opt() 
    # 객체 저장 list 선언
    monitors = []
    print(mode)
    for svc in svcs:
        #print(mon)
        svcnm = svc.split('-')[0]
        if svcnm == 'hdfs':
            monitors.append(recognizer.HdfsSvcRecog(config))
        elif svcnm == 'hadoop':
            monitors.append(recognizer.HadoopSvcRecog(config))
        elif svcnm == 'hive':
            monitors.append(recognizer.HiveSvcRecog(config))
        else:
            monitors.append(recognizer.SvcRecog(svc, config))
   
    for i in monitors:
        svcnm = i.get_svcname()
        i.is_port_open()
        i.is_pid_exist()
        i.set_heap_size()

        if svcnm == 'hdfs' or svcnm == 'hadoop':
            i.set_nodes()
        elif svcnm == 'hive':
            i.run_dummy('set mapred.job.queue.name=default;select count(*) from default;') 
        else:
            pass
        i.detect_error()
   
    # mail config를 가져오기 위해서..
    conf = ConfigParser.RawConfigParser()
    conf.read(config)
    tbl_res = ''
    jira_res = ''
    for m in mode:
        if m == 'mail':
            for i in monitors:
                tbl_res += i.get_restable()
            mail_file = commons.generate_mail(m, os.path.join(os.path.dirname(file_path),'lib',
                                      m+'_template.html'), 'service  monitoring' ,
                                      tbl_res, socket.gethostname(), file_path)
            commons.send_mail(conf.get('alert', 'mail_sub'), conf.get('alert', 'mail_send'),
                      conf.get('alert', 'mail_recv') , mail_file, m)
        elif m == 'jira':
            for i in monitors:
                jira_res += i.get_jiratable() 
            commons.send_mail(conf.get('alert', 'jira_ticket'), conf.get('alert','jira_send'),
                      conf.get('alert', 'jira_recv'), jira_res, m)
