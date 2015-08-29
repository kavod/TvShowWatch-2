#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import requests
import json
import torrentProvider
import logging

torrentProvider.TRACKER_CONF.append({'id':'t411','name':'T411','url':'https://api.t411.io','param':['username','password']})

def connect_t411(self):
	if not self.token: #If no token, let's connect
		req = requests.post(self.provider['url']+"/auth", {'username': self.param['username'], 'password': self.param['password']}, verify=False)
		if 'code' not in req.json().keys():
			self.token = req.json()['token']
			self.uid = req.json()['uid']
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
		req = requests.post(self.provider['url']+"/users/profile/" + self.uid,headers={"Authorization": self.token}, verify=False)
		return ('code' not in req.json().keys())
			
def search_t411(self, search):
	if not self.test():
		self.connect()
	result = requests.post(self.provider['url']+"/torrents/search/" + search,headers={"Authorization": self.token}, verify=False).json()
	logging.debug('%s', result)
	if 'torrents' in result.keys():
		result = result['torrents']
		logging.debug('%s torrents found', int(len(result)))
		result = filter(self.filter_t411,result)
		return result
	else:
		return []
                    
def download_t411(self,torrent_id):
	logging.debug("/torrents/download/"+str(torrent_id))
	stream = requests.post(self.provider['url']+"/torrents/download/"+str(torrent_id),headers={"Authorization": self.token}, stream=True, verify=False)
	with open(self.tmppath + '/file.torrent', 'wb') as f:
		for chunk in stream.iter_content(chunk_size=1024): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
		     		f.flush()
	return 'file://' + self.tmppath + '/file.torrent'
	
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
