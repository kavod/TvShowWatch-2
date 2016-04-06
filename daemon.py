#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import threading
import time
import logging
import TSWmachine

def daemon():
	while True:
		"""try:
			logging.error('run!')
			TSWmachine.run()
		except:
			pass
		time.sleep(3)"""
		
		t = threading.Timer(3.0,TSWmachine.run)
		t.daemon = True
		t.start()
		while t.isAlive():
			pass

if __name__ == '__main__':
	daemon()
