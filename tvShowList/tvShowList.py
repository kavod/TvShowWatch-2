#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import JSAG
#import myTvDB

class tvShowList(object):
	def __init__(self, l_tvShows=[]):
		self.schema = JSAG.loadParserFromFile("tvShowList/tvShowList.jschem")
		self.tvList = JSAG.JSAGdata(self.schema,value=l_tvShows)
		
	def loadFile(self,filename,path=[]):
		self.tvList.setFilename(filename,path=path)
		try:
			self.tvList.load()
		except IOError:
			print "File does not exist. Creating a new one"
			self.tvList.save()

	def __len__(self):
		if self is None:
			return 0
		else:
			return len(self.tvList)
