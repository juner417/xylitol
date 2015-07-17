#!/usr/bin/python
#-*- coding: utf-8 -*-
import os, sys
import logging, time, re, socket
from lib import *

'''
Description
    file indent = 4 space
'''
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s][%(levelname)s] %(message)s')

if __name__=='__main__':

    if len(sys.argv) < 2:
        commons.print_usage()
        exit(2)

    config = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          'conf','fail_detection.ini')
    svc, mode = commons.read_opt()
    
    logging.info('config : %s' % (config))
    logging.info('svc : %s' % (svc))
    logging.info('mode : %s' % (mode))

    if svc == 'hadoop':
        print(svc)

    elif svc == 'hive':
        print(svc)

    else:
        commons.print_usage()
        exit(2)



    app_res
    
