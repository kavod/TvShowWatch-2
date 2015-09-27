#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import os
import subprocess

class color:
   PURPLE = '\033[95m'
   WHITE = '\033[97m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class msg:
	INIT = "{0:80}[     ]"
	OK = "\r{0:80}[ " + color.GREEN + "OK" + color.END + "  ]"
	ERROR = "\r{0:80}[" + color.RED + "ERROR" + color.END + "]"
	NEWLINE = "\n"

FNULL = open(os.devnull, 'w')

if len(sys.argv) < 3:
	sys.exit(1)
label=sys.argv[1]
cmd=sys.argv[2:]

print(msg.INIT.format(label)),
sys.stdout.flush()

result = subprocess.call(cmd,stdout=FNULL, stderr=subprocess.STDOUT)

if result==0:
	print msg.OK.format(label)
	sys.exit(0)
else:
	print msg.ERROR.format(label)
	sys.exit(result)
