#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import re

class TSWdirectories(dict):
	def __init__(self,filename=None):
		dict.__init__(self)
		if filename is not None:
			if not isinstance(filename,basestring):
				raise TypeError("filename must be a string")
			if not os.path.isfile(filename):
				raise Exception("{0} doest not exists".format(filename))
			with open(filename) as f:
				content = f.readlines()
			self._parseContent(content)
				
	def _parseLine(self,line):
		match = re.search(r'^(\w+)="([^"]+)"$',line)
		if match is None:
			match = re.search(r'^(\w+)=([^"]+)$',line)
			if match is not None:
				self[match.group(1)] = int(match.group(2))
		else:
			self[match.group(1)] = match.group(2)
			if match.group(1).find("_path") > 0:
				path = os.path.abspath(os.path.expanduser(match.group(2)))
				self[match.group(1)] = path
				if not os.path.isdir(path):
					os.makedirs(path)
	
	def _parseContent(self,content):
		for line in content:
			self._parseLine(line)
