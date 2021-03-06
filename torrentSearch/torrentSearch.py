#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import torrentProvider
import JSAG3

torrentProvider.loadProviders()

class torrentSearch(JSAG3.JSAG3):
	def __init__(self,id="torrentSearch",dataFile=None,verbosity=False):
		curPath = os.path.dirname(os.path.realpath(__file__))
		self.providers = dict()
		self.verbosity=verbosity
		JSAG3.JSAG3.__init__(self,
			id=id,
			schemaFile=curPath+"/torrentSearch.jschem",
			optionsFile=curPath+"/torrentSearch.jopt",
			dataFile=dataFile,
			verbosity=verbosity
		)

	def loadConfig(self,confFile,path=[]):
		self.addData(confFile)
		self.logger.debug("Data loaded: {0}.".format(unicode(self.data)))

	def search(self,pattern):
		self.logger.debug("Search pattern: {0}.".format(unicode(pattern)))
		if 'providers' not in self.data.keys() or len(self.data['providers'])<1:
			self.logger.error("[torrentSearch] No torrent provider setup")
			return None
		global_keywords = self.data['keywords'] if 'keywords' in self.data.keys() else []
		if len(global_keywords)<1:
			global_keywords=['']
		if pattern is None or unicode(pattern) == "":
			raise Exception("Empty pattern")
		pattern = unicode(pattern)
		for provider in self.data['providers']:
			provID = unicode(provider['provider_type'])
			self.connect_provider(provID)
			for keyword in global_keywords:
				if len(keyword)>0:
					keyword = ' '+keyword
				query = "{0}{1}".format(pattern,keyword)

				if 'keywords' in provider.keys() and len(provider['keywords']) > 0:
					queries = ["{0} {1}".format(query,keyword) for keyword in provider['keywords']]
				else:
					queries = [query]
				for query in queries:
					try:
						result = self.search_query(provID,query)
					except:
						self.logger.info("Timeout from {0}".format(unicode(provID)))
						continue
					if len(result)<1:
						continue
					return result
		return None

	def search_query(self,provID,query):
		torProv = self.providers[provID]
		self.logger.debug("Query sent to {0}: '{1}'".format(unicode(provID),unicode(query)))
		result = torProv.search(query)
		result = filter(torProv.filter,result)
		self.logger.info( "Search of \033[1m{0}\033[0m on \033[1m{1}\033[0m".format(query,provID))
		if len(result) < 1:
			self.logger.info( " > No result")
			return []
		elif len(result) == 1:
			self.logger.info( " > 1 result")
		elif len(result) > 1:
			self.logger.info( " > {0} results".format(unicode(len(result))))
		result = torProv.select_torrent(result)
		result['provider'] = provID
		return result


	def connect_provider(self,provID):
		provider = [provider for provider in self.data['providers'] if unicode(provider['provider_type']) == provID][0]
		self.logger.info( "Connecting provider: ".format(unicode(self.data['providers'])))
		if provID not in self.providers.keys():
			self.providers[provID] = torrentProvider.torrentProvider(
				trackerID=provID,
				param_data=provider['authentification'] if 'authentification' in provider.keys() else None,
				SSLverif=not(self['disableSSL']) if'disableSSL' in self.keys() else True,
				verbosity=self.verbosity
			)

	def download(self,tor):
		availProviders = [prov['id'] for prov in torrentProvider.TRACKER_CONF]
		if tor is None:
			raise Exception("No torrent to be downloaded")
		if 'provider' not in tor.keys():
			raise Exception("Torrent provider is missing")
		if tor['provider'] not in availProviders:
			raise Exception("Unknown torrent provider: {0} ({1})\nKnown providers: {2}".format(tor['provider'],type(tor['provider']),unicode(availProviders)))
		return self.providers[tor['provider']].download(tor['id'])

	def test(self):
		for provider in self.providers.values():
			provider.connect()
			provider.test()
