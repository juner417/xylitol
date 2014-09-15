#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import MySQLdb
import re

# cretae table function
def create_table(table):
	tbnm = table
	pinfl = os.path.join(os.path.dirname(os.path.abspath(__file__)),  "../", ".pin/passwd")
	
	search_term = 'mysql'
	f = open(pinfl, 'r')
	lines = f.readlines()
	
	for line in lines:
		if re.search(search_term, line):
			pin = line.split('=')[1].split('\n')[0]

	try:
		print('db connection pin : ' + pin )
		print pin
		db = MySQLdb.connect(host='dev-ocean1', port=3306, user='junermysql', passwd=pin, db='junerdev') 
		cur = db.cursor()
		print('table create')
		#sql = ''' CREATE TABLE IF NOT EXISTS %s
		#		(no int, name char(16), dept char(16)) ''' % tbnm
		sql = ''' CREATE TABLE IF NOT EXISTS %s
				(id int NOT NULL AUTO_INCREMENT, name char(30) NOT NULL, email char(30), passwd char(16), PRIMARY KEY (id) ) ''' % tbnm
		cur.execute(sql)
		print('table create done')
		db.commit()
		db.close()
	except IOError as e:
		print "I/O error"

# db 접속 후 테이블 생성
if __name__=="__main__":
	create_table('user')
