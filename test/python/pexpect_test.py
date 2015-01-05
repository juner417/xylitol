#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, subprocess, pexpect

msg = 'Are you sure you want to continue connecting'
con_msg = 'rcp -r ./test/ acc@server:~/'

child = pexpect.spawn(con_msg)
#index = child.expect([msg, 'password:', pexpect.EOF, pexpect.TIMEOUT], 1)
index = child.expect([msg, 'password:', pexpect.EOF, pexpect.TIMEOUT])

if index  == 0:
    print 'index==0'
    child.sendline('yes')
    index = child.expect([msg, 'password:', pexpect.EOF, pexpect.TIMEOUT])

if index == 1:
    print 'index == 1'
    child.sendline('pinno')
    index = child.expect([pexpect.EOF, pexpect.TIMEOUT])
elif index == 2:
    print 'cannot connect to ' + con_msg
    sys.exit(0)

#child.expect('password:')
#try:
	#child.interact()
#except:
	#pass

# reference
#http://carpedm20.blogspot.kr/2013/05/python-subprocess.html
#http://linux.byexamples.com/archives/346/python-how-to-access-ssh-with-pexpect/
#http://jmnote.com/wiki/Python_pexpect_%EC%98%88%EC%A0%9C
