#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import requests
import json
import re
import torrentProvider
import logging
import tempfile
from simplejson.decoder import JSONDecodeError

torrentProvider.TRACKER_CONF.append({'id':'t411','name':'T411','url':'https://api.t411.ch','param':['username','password']})

def connect_t411(self):
	if not self.token: #If no token, let's connect
		req = requests.post(self.provider['url']+"/auth", {'username': self.param['username'], 'password': self.param['password']}, verify=False, timeout=5)
		try:
			result = req.json()
		except JSONDecodeError:
			raise Exception("Invalid response from server: {0}".format(unicode(req)))
		if 'code' not in result.keys():
			self.token = result['token']
			self.uid = result['uid']
			return True
		else:
			raise requests.exceptions.ConnectionError('Unable to login on T411. Please check username/password')
	else: #If token exist, let's test connection
		if self.test_t411():
			return True
		else:#If error code returned, token is expired. So let's erase it and reconnect
			self.token = ''
			return self.connect_t411()

def test_t411(self):
	if not self.token: 
		return False
	else: 
		req = requests.post(self.provider['url']+"/users/profile/" + self.uid,headers={"Authorization": self.token}, verify=False, timeout=5)
		try:
			result = req.json()
		except JSONDecodeError:
			raise Exception("Invalid response from server: {0}".format(unicode(req)))
		return ('code' not in result.keys())
			
def search_t411(self, search):
	if not self.test():
		self.connect()
	try:
		search = re.sub(r'(S\d{2}E\d{2})',r'*\1*',search) # Fix search by episode issue on T411
		result = requests.post(self.provider['url']+"/torrents/search/" + search,headers={"Authorization": self.token}, verify=False, timeout=5)
		result = result.json()
	except JSONDecodeError:
		Exception("Unable to parse JSON: {0}".format(result))
	logging.debug('%s', result)
	if 'torrents' in result.keys():
		result = result['torrents']
		logging.debug('%s torrents found before filtering', int(len(result)))
		result = filter(self.filter_t411,result)
		logging.debug('%s torrents found after filtering', int(len(result)))
		return result
	else:
		return []
                    
def download_t411(self,torrent_id):
	logging.debug("/torrents/download/"+str(torrent_id))
	stream = requests.post(self.provider['url']+"/torrents/download/"+str(torrent_id),headers={"Authorization": self.token}, stream=True, verify=False, timeout=5)
	tmpFile = unicode(tempfile.mkstemp('.torrent')[1])
	with open(tmpFile, 'wb') as f:
		for chunk in stream.iter_content(chunk_size=1024): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
		     		f.flush()
	return tmpFile
	
def select_t411(self,result):
	logging.debug(result)
	return sorted(result, key=lambda tor: int(tor[u'times_completed']), reverse=True)[0]
	
def filter_t411(self,tor):
	return int(tor['seeders']) > 0 and tor['isVerified'] == '1' and int(tor['times_completed']) > 0

setattr(torrentProvider.torrentProvider,'connect_t411',connect_t411)
setattr(torrentProvider.torrentProvider,'test_t411',test_t411)
setattr(torrentProvider.torrentProvider,'search_t411',search_t411)
setattr(torrentProvider.torrentProvider,'download_t411',download_t411)
setattr(torrentProvider.torrentProvider,'filter_t411',filter_t411)
setattr(torrentProvider.torrentProvider,'select_t411',select_t411)
