#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys, ConfigParser, getopt

def print_usage():

    print ('WARN) check the args')
    print ('USAGE) python your sctipt.py -c config')
    sys.exit(1)

def getconf(filename, title, name):
    
    ini_file = filename
    config = ConfigParser.RawConfigParser()
    config.read(ini_file)

    value = config.get(title, name)
    return value

def read_opt():
    
    try: 
        opt, args = getopt.getopt(sys.argv[1:], 'c:')
    except getopt.GetoptError as err:
        print_usage()
        sys.exit(2)

    for op, p in opt:
        if op == '-c':
            configfile = p
        else:
            print_usage()
            sys.exit(2)
    
    return configfile


