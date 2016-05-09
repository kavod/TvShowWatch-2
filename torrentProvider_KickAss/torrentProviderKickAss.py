#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import requests
import json
import torrentProvider
import logging
import tempfile

torrentProvider.TRACKER_CONF.append({'id':'kat','name':'KickAss Torrents','url':"https://kat.cr",'param':[]})

def connect_kat(self):
	return self.test_kat()

def test_kat(self,verify=True):
	req = requests.post(self.provider['url']+"/json.php", verify=verify)
	return ('title' in req.json().keys())
			
def search_kat(self, search,verify=True):
	if not self.test():
		self.connect()
	params = {'q':search}
	result = requests.post(self.provider['url']+"/json.php",params=params, verify=verify)
	result = result.json()
	logging.debug('%s', result)
	if 'list' in result.keys():
		result = result['list']
		logging.debug('%s torrents found before filter', int(len(result)))
		result = filter(self.filter_kat,result)
		logging.debug('%s torrents found after filter', int(len(result)))
		return result
	else:
		return []
                    
def download_kat(self,torrent_id,verify=True):
	logging.debug(unicode(torrent_id))
	stream = requests.get(unicode(torrent_id), stream=True, verify=verify, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/43.0.2357.130 Chrome/43.0.2357.130 Safari/537.36'})
	tmpFile = unicode(tempfile.mkstemp('.torrent')[1])
	with open(tmpFile, 'wb') as f:
		for chunk in stream.iter_content(chunk_size=1024): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
		     		f.flush()
	return tmpFile
	
def select_kat(self,result):
	logging.debug(result)
	return {'id':sorted(result, key=lambda tor: int(tor[u'votes']), reverse=True)[0]['torrentLink']}
	
def filter_kat(self,tor):
	return int(tor['seeds']) > 0 and tor['verified'] == 1 and int(tor['votes']) > 0

setattr(torrentProvider.torrentProvider,'connect_kat',connect_kat)
setattr(torrentProvider.torrentProvider,'test_kat',test_kat)
setattr(torrentProvider.torrentProvider,'search_kat',search_kat)
setattr(torrentProvider.torrentProvider,'download_kat',download_kat)
setattr(torrentProvider.torrentProvider,'filter_kat',filter_kat)
setattr(torrentProvider.torrentProvider,'select_kat',select_kat)
