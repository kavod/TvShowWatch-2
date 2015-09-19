#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import torrentProvider
import JSAG

torrentProvider.loadProviders()

class torrentSearch(object):
	def __init__(self):
		self.confSchema = JSAG.loadParserFromFile("torrentSearch/torrentSearch.jschem")
		self.conf = JSAG.JSAGdata(configParser=self.confSchema,value={})
		
	def loadConfig(self,confFile):
		self.conf.setFilename(confFile)
		try:
			self.conf.load()
		except:
			print "File does not exist. Creating a new one"
			self.conf.save()
	def cliConf(self):
		self.conf.cliCreate()
		self.conf.proposeSave(display=True)
		
	def displayConf(self):
		self.conf.display()
		
	def search(self,pattern):
		if pattern is None or str(pattern) == "":
			raise Exception("Empty pattern")
		pattern = str(pattern)
		for provider in self.conf['providers']:
			torProv = torrentProvider.torrentProvider(unicode(provider['id']),provider['config'] if 'config' in provider.keys() else None)
			for keyword in self.conf['keywords']:
				query = "{0} {1}".format(pattern,keyword)
				result = torProv.search(query)
				result = torProv.select_torrent(result)
				print "Search of \033[1m{0}\033[0m on \033[1m{1}\033[0m".format(query,provider['id'])
				if len(result) < 1:
					print " > No result"
					continue
				elif len(result) == 1:
					print " > 1 result"
				elif len(result) > 1:
					print " > {0} results".format(str(len(result)))
				torProv.download(result['id'])
				break
			if len(result) < 1:
				continue
			else:
				break
					
					
		
