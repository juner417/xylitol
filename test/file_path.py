#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys

file_path = os.path.abspath(__file__)
file_abs_path = os.path.dirname(file_path)
file_abs_path_dir = os.path.dirname(__file__)
pinfl = os.path.join(os.path.dirname(os.path.abspath(__file__)),  "../", ".pin/passwd")

print(file_path)
print(file_abs_path)
print(file_abs_path_dir)
print(pinfl)
