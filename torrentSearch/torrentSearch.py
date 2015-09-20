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
		self.providers = dict()
		
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
		if pattern is None or unicode(pattern) == "":
			raise Exception("Empty pattern")
		pattern = unicode(pattern)
		for provider in self.conf['providers']:
			provID = unicode(provider['id'])
			self.providers[provID] = torrentProvider.torrentProvider(provID,provider['config'] if 'config' in provider.keys() else None)
			torProv = self.providers[provID]
			for keyword in self.conf['keywords']:
				query = "{0} {1}".format(pattern,keyword)
				result = torProv.search(query)
				result = filter(torProv.filter,result)
				print "Search of \033[1m{0}\033[0m on \033[1m{1}\033[0m".format(query,provider['id'])
				if len(result) < 1:
					print " > No result"
					continue
				elif len(result) == 1:
					print " > 1 result"
				elif len(result) > 1:
					print " > {0} results".format(unicode(len(result)))
				result = torProv.select_torrent(result)
				result['provider'] = provID
				return result
		return None
		
	def download(self,tor):
		availProviders = [prov['id'] for prov in torrentProvider.TRACKER_CONF]
		if tor is None:
			raise Exception("No torrent to be downloaded")
		if 'provider' not in tor.keys():
			raise Exception("Torrent provider is missing")
		if tor['provider'] not in availProviders:
			raise Exception("Unknown torrent provider: {0} ({1})\nKnown providers: {2}".format(tor['provider'],type(tor['provider']),unicode(availProviders)))
		self.providers[tor['provider']].download(tor['id'])
					
					
		
