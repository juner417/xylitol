#!/usr/bin/python
#-*- coding: utf-8 -*-

import os, sys
import ConfigParser, getopt, logging, datetime, socket, getpass, types
import sendmail

logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s][%(levelname)s] %(message)s')

def print_usage():
    
    print ('WARN) check the args')
    print ('USAGE) python check.py [option]')
    print ('''option : -s [service:hadoop,hdfs,hive|all]
        -m [mail,jira]''')
    sys.exit(1)

def getconf(filename, title, name):

    ini_file = filename
    config = ConfigParser.RawConfigParser()
    config.read(ini_file)
    
    value = config.get(title, name)
    return value

def read_opt():

    try:
        opt, args = getopt.getopt(sys.argv[1:], 's:m:')
    except getopt.GetoptError as err:
        print_usage()
        sys.exit(2)

    mode = 'stdout'
    for op, p in opt:
        if op == '-s':
            if p == 'all':
                svc = getconf(os.path.join(os.path.dirname(
                              os.path.abspath(__file__)), 
                              '../conf', 'fail_detection.ini'), 'svc', 'svc_list').split(',')
            else:
                svc = p.split(',')
            
        elif op == '-m':
            mode = p.split(',')
        else:
            print_usage()
            sys.exit(2)

    return svc, mode

def generate_mail(mode, html_file, report_sub, contents, hostname, script):
    # generate mail 
    acc = getpass.getuser()

    f = open(html_file, 'r')
    msg = f.read().replace('\n','\r\n')
    msg_tmp = msg.replace("[REPORT_SUBJECT]",report_sub)
    msg_tmp = msg_tmp.replace("[DT]", datetime.datetime.isoformat(datetime.datetime.now()))
    msg_tmp = msg_tmp.replace("[TABLE_CONTENTS]", contents )
    msg_tmp = msg_tmp.replace("[HOST]", hostname)
    msg_tmp = msg_tmp.replace("[SCRIPT]", script)
    msg_tmp = msg_tmp.replace("[ACC]", acc)

    f.close()

    f = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
             '..','logs','alert_'+mode+'.html' ), 'w')
    f.write(msg_tmp)
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','logs','alert_'+mode+'.html' )

    return file_path

def create_table(mail_flag, title=None):
    #결과 테이블의 header =0, tail =1 생성
    if mail_flag == 0:
        res = '''<table><tr><td colspan=2 style='border:0px;vertical-align:top;'>
<span class='title'> %s </span></br>
</td></tr>
<tr><td style='border:0px;vertical-align:top;'>
<table width="500" style="table-layout:fixed">
''' % title
    else:
        res = '''</table>
</td><td style='border:0px;vertical-align:bottom;'>
</td></tr></table></br>'''

    return res

def res_mapping(subject, result):
    #조회 결과를 html table로 생성하여 return
    if subject == 'comment':
        keys = result.keys()
        # comment에 total_result를 맨 위로 올리기 위해서 조작
        keys.remove('total_result')
        res = '''<tr><td class='hdr' width="130" style="table-layout:fixed">%s</td><td align=left>''' % (subject)
        res += '''%s<br>''' % result['total_result']
        # total_result를 제외하고 맵핑
        for key in keys:
            if isinstance(result[key], types.ListType):
                for i in result[key]:
                    res += '''%s<br>''' % i
            else:
                res += '''%s<br>''' % result[key]
        res += '</td></tr>'

    else:
        if isinstance(result, types.ListType):
            span = len(result)
            res = '''<tr><td class='hdr' width="130" style="table-layout:fixed" rowspan="%s">%s</td>
<td align=left>%s</td></tr>''' %(span, subject, result[0])
            for i in range(1,span):
                res += '''<tr><td align=left>%s</td></tr>''' % (result[i])
            #res += ""
        else:
            res = '''<tr><td class='hdr' width="130" style="table-layout:fixed">%s</td>
<td align=left>%s</td></tr> ''' % (subject, result)

    return res

def create_res(keys, result, errmsg):
    # create error email
    table = ''
    for i in keys:
        if i == "comment":
            table += res_mapping(i, errmsg)
        else:
            table += res_mapping(i, result[i])

    return table

def send_mail(title, send, recv, mailfile, mode):
    # send to jira comment
    if mode == 'mail':
    # 메일 전송
        #logging.info("mail success %s" % mailfile)
        f = open(mailfile, 'r')
        msg = f.read().replace('\n','\r\n')
        args = ['-v', 'mailserver','-s',title, '-f',send, '-r',recv, '-m',msg , '-t', 'html']
        f.close()
        logging.info("send mail : %s" % mailfile)
    else: 
        args = ['-v', 'send mail','-s',title, '-f',send, '-r',recv, '-m',mailfile  ]
        logging.info("send mail : Jira comment")
        
    sendmail.sendmail(args)
