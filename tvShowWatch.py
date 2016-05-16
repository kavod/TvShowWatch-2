#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import sys
import time
import tempfile
#import subprocess
import server
import utils.TSWdirectories

curPath = os.path.dirname(os.path.realpath(__file__))
directories = utils.TSWdirectories(curPath+'/utils/directory.conf')
tmpPath = os.path.abspath(directories['tmp_path'])
pid_file = tmpPath + '/TSW2.PID'

def daemon_status():
	if os.path.isfile(pid_file):
		pid = open(pid_file,'r').read()
		try:
			os.kill(int(pid), 0)
			return True
		except:
			os.remove(pid_file)
	return False

def startDaemon():
	curPath = os.path.dirname(os.path.realpath(__file__))
	# Fork and die
	pid = os.fork()
	if pid == 0: #The first child
		#os.chdir("/")
		os.setsid()
		os.umask(0)
		pid2 = os.fork()
		if pid2 == 0:
			server.main()
			#subprocess.call(["python",curPath + '/server.py'])
	sys.exit()

def stopDaemon():
	if os.path.isfile(pid_file):
		pid = open(pid_file,'r').read()
		try:
			os.kill(int(pid), 15)
			if not wait_for_status(False,10):
				os.kill(int(pid), 9)
			os.remove(pid_file)
		except:
			pass

def wait_for_status(status,retry):
	while retry > 0:
		if not daemon_status():
			return True
		retry -= 1
		time.sleep(1)
	return False

if __name__ == '__main__':
	if sys.argv[1] == 'start':
		if daemon_status():
			print("%s is already running" % ("TvShowWatch2"))
			sys.exit()
		else:
			print("Starting %s" % ("TvShowWatch2"))
			startDaemon()
			sys.exit()
	elif sys.argv[1] == 'stop':
		if daemon_status():
			print "Stopping %s" % ("TvShowWatch2")
			stopDaemon()
			sys.exit()
		else:
			print "%s is not running" % ("TvShowWatch2")
			sys.exit()
	elif sys.argv[1] == 'status':
		if daemon_status():
			print "%s is running" % ("TvShowWatch2")
			sys.exit()
		else:
			sys.exit("%s is not running" % ("TvShowWatch2"))
	elif sys.argv[1] == 'restart':
		if daemon_status():
			print "Stopping %s" % ("TvShowWatch2")
			stopDaemon()
		else:
			print "%s is not running" % ("TvShowWatch2")
		if daemon_status():
			print("%s is still running" % ("TvShowWatch2"))
			sys.exit()
		else:
			print("Starting %s" % ("TvShowWatch2"))
			startDaemon()
			sys.exit()
