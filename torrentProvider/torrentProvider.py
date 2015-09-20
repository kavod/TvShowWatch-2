#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import re,os
import string
import logging
from importlib import import_module

TRACKER_CONF = [
		{'id':'none','name':'No tracker, only manual push','url':"",'param':[]}
	]
	
TMPPATH = "/tmp"

def check_provider(trackerID):
	# Selecting requested provider
	provider = [x for x in TRACKER_CONF if x['id'] == trackerID]
	if len(provider) < 1:
		providers = [x['id'] for x in TRACKER_CONF]
		raise Exception('Provider ' + str(trackerID) + ' not recognized (installed providers are ' + str(providers))
		return False
	else:
		return provider[0]

class torrentProvider:
	def __init__(self,trackerID,param_data,tmppath = TMPPATH ):
		self.provider = {} 		# Provider data
		self.token = ''			# If required by provider, authentification token
		self.param = {}			# If required by provider, extra parameters (like username / password)
		self.tmppath = tmppath

		# Selecting requested provider
		try:
			self.provider = check_provider(trackerID)
		except Exception as e:
			raise Exception(e)

		# Populating paramerters
		for param in self.provider['param']:
			if param in param_data.keys():
				self.param[param] = param_data[param]
			else:
				raise Exception("Missing parameter: "+param)

	def connect(self):
		return getattr(self, "connect_"+self.provider['id'])()
		
	def connect_none(self):
		self.token = 'ok'
		return True
		
	def test_none(self):
		return True
		
	def test(self):
		return getattr(self, "test_"+self.provider['id'])()
		
	def search_none(self,search):
		return []

	def search(self,search):
		search = re.sub('[%s]' % re.escape(string.punctuation), '', search)
		return getattr(self, "search_" + self.provider['id'] )(search)
		
	def download_none(self,torrent_id):
		return False
		
	def download(self,torrent_id):
		return getattr(self, "download_" + self.provider['id'] )(torrent_id)
		
	def select_none(self,result):
		logging.debug(result)
		return result[0]

	def select_torrent(self,result):
		return getattr(self, "select_" + self.provider['id'] )(result)
		
	def filter_none(self,tor):
		return []

	def filter(self,tor):
		return getattr(self, "filter_" + self.provider['id'] )(tor)

#extensions = os.walk(os.path.dirname(os.path.abspath(__file__))+"/../")
#for ext in [x[0] for x in extensions if x[0][0:18] == './torrentProvider_']:
#	import_module(ext)
def loadProviders():
	extensionPrefix = 'torrentProvider_'
	thedir = os.path.dirname(os.path.abspath(__file__))+"/../"
	for ext in [x for x in os.listdir(thedir) if os.path.isdir(os.path.join(thedir, x)) and x[0:len(extensionPrefix)] == extensionPrefix]:
		import_module(ext)

