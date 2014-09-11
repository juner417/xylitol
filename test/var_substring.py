#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re

pinfl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../", ".pin/passwd")

f = open(pinfl, 'r')
lines = f.readlines()
for line in lines:
	print(line)
	res = re.search('mysql=',  line).group(0)
	cut = line.split('=')[1]
	print(res)
	print(cut)
