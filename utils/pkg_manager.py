#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import os
import subprocess

PACKAGES = {
	'JSAG':{
		'install':[
			['wget',"https://github.com/kavod/jsonSchemaAppGenerator/releases/download/v1.5.10/JSAG.tgz",'-q'],
			['tar','zxf','JSAG.tgz'],
			['rm','JSAG.tgz']
				],
		'uninstall':[
			['rm','-rf','JSAG']
				]
			}
		}

if len(sys.argv) < 3:
	sys.exit(1)

action = unicode(sys.argv[1])
pkg = unicode(sys.argv[2])

if pkg not in PACKAGES.keys():
	sys.exit(1)

if action not in PACKAGES[pkg]:
	sys.exit(1)

FNULL = open(os.devnull, 'w')

for cmd in PACKAGES[pkg][action]:
	subprocess.call(cmd,stdout=FNULL, stderr=subprocess.STDOUT)
