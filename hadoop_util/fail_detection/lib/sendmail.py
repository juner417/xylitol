#!/usr/bin/env python
#-*- coding: utf-8 -*-

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
import os, sys, getopt, base64
from smtplib import SMTP

reload(sys)
sys.setdefaultencoding('utf-8')

def help():
    print "Usage :",sys.argv[0],"-v 'snmp-server' -s 'subject' -f 'from' -r 'recipient' -m 'message' [-t 'plain or html' -c 'cc' -a 'attachment']"
    print "       ",sys.argv[0],"-v 'snmp-server' -s 'subject' -f 'from' -r 'recipient' [-c 'cc' -a 'attachment'] << EOF"
    
def sendmail(argv):
    snmp_server=''
    mail_subject = ''
    mail_from = ''
    mail_to = ''
    mail_cc = ''
    mail_body = ''
    mail_attachment = ''
    mail_type = 'plain'
    
    try:
        opts, args = getopt.getopt(argv,"hv:s:f:r:m:c:a:t:");
    except getopt.GetoptError:
        #help()
        sys.exit(1)
        
    for opt, arg in opts:
        if opt == '-h':
            help()
            sys.exit();
        elif opt == '-v':
            snmp_server = arg
        elif opt == '-s':
            mail_subject = arg
        elif opt == "-f":
            mail_from = arg
        elif opt == "-r":
            mail_to = arg
        elif opt == "-c":
            mail_cc = arg
        elif opt == "-m":
            mail_body = arg
        elif opt == "-a":
            mail_attachment = arg
        elif opt == "-t" and arg == 'html':
            mail_type = 'html'
    
    if len(mail_subject) == 0 or len(mail_from) == 0 or len(mail_to) == 0:
        help()
        sys.exit(2)
    
    if len(mail_body) ==0:
        mail_body = "".join(open('/dev/stdin', 'r').readlines()).replace('\n', '\r\n')

    msg = MIMEMultipart()
    msg['Subject'] = '=?utf-8?B?' + base64.standard_b64encode(mail_subject) + '?='
    msg['From'] = mail_from
    msg['To'] = COMMASPACE.join(mail_to.split(','))
    msg['CC'] = COMMASPACE.join(mail_cc.split(','))
    msg['Date'] = formatdate(localtime = True)
    msg.attach(MIMEText(mail_body,mail_type))
    
    if len(mail_attachment) > 0:
        for f in mail_attachment.split(','):
            part = MIMEBase('text', "plain")
            part.set_payload(open(f, "r").read())
            part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
            msg.attach(part)
                
    smtp_serv = SMTP(snmp_server)
    smtp_serv.sendmail(mail_from, mail_to.split(',')+mail_cc.split(','), msg.as_string())
    smtp_serv.close()
    print "Successfully sent email"
        
if __name__ == "__main__":
    sendmail(sys.argv[1:])
