#!/usr/bin/python
#-*- coding: utf-8 -*-

import os, sys
import ConfigParser, getopt, logging, datetime, socket, getpass
import sendmail

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s][%(levelname)s] %(message)s')

def print_usage():
    
    print ('WARN) check the args')
    print ('USAGE) python check.py [option]')
    print ('''option : -s [service:HADOOP,HIVE]
        -m [mail,stdout]''')
    sys.exit(1)

def getconf(filename, title, name):

    ini_file = filename
    config = ConfigParser.RawConfigParser()
    config.read(ini_file)
    
    value = config.get(title, name)
    return value

def read_opt():

    try:
        opt, args = getopt.getopt(sys.argv[1:], 's:m')
    except getopt.GetoptError as err:
        print_usage()
        sys.exit(2)

    mode = 'stdout'
    for op, p in opt:
        if op == '-s':
            svc = p
        elif op == '-m':
            mode = 'mail'
        else:
            print_usage()
            sys.exit(2)

    return svc, mode

def generate_html(mode, html_file, report_sub, contents, hostname, script_path, script):
    # generate mail 
    acc = getpass.getuser()
    f = open(html_file, 'r')
    msg = f.read().replace('\n','\r\n')
    msg_tmp = msg.replace("[REPORT_SUBJECT]",report_sub)
    msg_tmp = msg_tmp.replace("[DT]", datetime.datetime.isoformat(datetime.datetime.now()))
    msg_tmp = msg_tmp.replace("[TABLE_CONTENTS]", contents)
    msg_tmp = msg_tmp.replace("[HOST]", hostname)
    msg_tmp = msg_tmp.replace("[PATH]", script_path)
    msg_tmp = msg_tmp.replace("[SCRIPT]", script)
    msg_tmp = msg_tmp.replace("[ACC]", acc)

    #print(msg_tmp)
    f.close()

    f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
             '..','logs','alert_'+mode+'.html' ), 'w')
    f.write(msg_tmp)
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','logs','alert_'+mode+'.html' )

    return file_path

def send_mail(title, send, recv, mailfile):
    # send to jira comment
    # 메일 전송
    logging.info("mail success %s" % mailfile)
    f = open(mailfile, 'r')
    msg = f.read().replace('\n','\r\n')
    args = ['-v', 'mailserver','-s',title, '-f',send, '-r',recv, '-m',msg , '-t', 'html']
    sendmail.sendmail(args)
    f.close()
