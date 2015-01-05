#!/usr/bin/python 

import os, sys


def test(*args):
	for i in args:
		print(i)

if __name__=="__main__":
	arr=[1,2,3,4,5]
	test(*arr)
