#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import os
import subprocess
import getpass

PACKAGES = {
		'JSAG':{
			'install':
				[
					['wget',"https://github.com/kavod/jsonSchemaAppGenerator/releases/download/v1.6.1/JSAG.tgz",'-q'],
					['tar','zxf','JSAG.tgz'],
					['rm','JSAG.tgz']
				],
			'uninstall':
				[
					['rm','-rf','JSAG']
				],
			'root_install':
				[
					['wget',"https://github.com/kavod/jsonSchemaAppGenerator/releases/download/v1.6.1/JSAG.tgz",'-q'],
					['tar','zxf','JSAG.tgz'],
					['rm','JSAG.tgz']
				],
			'root_uninstall':
				[
					['rm','-rf','JSAG']
				]
			},
		'JSAG3':{
			'install':
				[
					['wget',"https://github.com/kavod/JSAG3/releases/download/v3.0.3/JSAG3.tgz",'-q'],
					['tar','zxf','JSAG3.tgz'],
					['rm','JSAG3.tgz']
				],
			'uninstall':
				[
					['rm','-rf','JSAG3']
				],
			'root_install':
				[
					['wget',"https://github.com/kavod/JSAG3/releases/download/v3.0.3/JSAG3.tgz",'-q'],
					['tar','zxf','JSAG3.tgz'],
					['rm','JSAG3.tgz']
				],
			'root_uninstall':
				[
					['rm','-rf','JSAG3']
				]
			},
		'python_packages':{
			'install':
				[
					['pip',"install",'--user','-r','requirements.txt']
				],
			'uninstall':
				[
					['true']
				],
			'root_install':
				[
					['pip',"install",'-r','requirements.txt']
				],
			'root_uninstall':
				[
					['true']
				]
			}
		}
		
if len(sys.argv) < 3:
	print "Missing argument"
	sys.exit(1)

action = unicode(sys.argv[1])
if getpass.getuser() == 'root':
	action = 'root_' + action
pkg = unicode(sys.argv[2])

if pkg not in PACKAGES.keys():
	print "Unknown package {0}".format(pkg)
	sys.exit(1)

if action not in PACKAGES[pkg]:
	print "Unknown action {0}".format(action)
	sys.exit(1)

FNULL = open(os.devnull, 'w')

for cmd in PACKAGES[pkg][action]:
	rtn = subprocess.call(cmd,stdout=FNULL, stderr=subprocess.STDOUT)
	if rtn > 0:
		sys.exit(rtn)
