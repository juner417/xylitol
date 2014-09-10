#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import MySQLdb

# cretae table function
def create_table(table):
	tbnm = table

	try:
		print('db connection')
		db = MySQLdb.connect(host='dev-ocean1', port=3306, user='junermysql', passwd='', db='junerdev')
		cur = db.cursor()
		print('table create')
		sql = ''' CREATE TABLE IF NOT EXISTS %s
				(no int, name char(16), dept char(16)) ''' % tbnm
		cur.execute(sql)
		print('table create done')
		db.commit()
		db.close()
	except IOError as e:
		print "I/O error"

# db 접속 후 테이블 생성
create_table()
