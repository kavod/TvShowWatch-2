#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import requests
import json
import torrentProvider
import logging

torrentProvider.TRACKER_CONF.append({'id':'kickass','name':'KickAss','url':"https://kickass.to",'param':[]})

def connect_kickass(self):
	return self.test_kickass()

def test_kickass(self):
	req = requests.post(self.provider['url']+"/json.php", verify=False)
	return ('title' in req.json().keys())
			
def search_kickass(self, search):
	if not self.test():
		self.connect()
	params = {'q':search}
	result = requests.post(self.provider['url']+"/json.php",params=params, verify=False)
	result = result.json()
	logging.debug('%s', result)
        if 'list' in result.keys():
                result = result['list']
                logging.debug('%s torrents found', int(len(result)))
                result = filter(self.filter_kickass,result)
                return result
        else:
                return []
                    
def download_kickass(self,torrent_id):
	logging.debug(str(torrent_id))
	stream = requests.get(str(torrent_id), stream=True, verify=False, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/43.0.2357.130 Chrome/43.0.2357.130 Safari/537.36'})
	with open(self.tmppath + '/file.torrent', 'wb') as f:
		for chunk in stream.iter_content(chunk_size=1024): 
			if chunk: # filter out keep-alive new chunks
				f.write(chunk)
		     		f.flush()
	return 'file://' + self.tmppath + '/file.torrent'
	
def select_kickass(self,result):
	logging.debug(result)
	return {'id':sorted(result, key=lambda tor: int(tor[u'votes']), reverse=True)[0]['torrentLink']}
	
def filter_kickass(self,tor):
	return int(tor['seeds']) > 0 and tor['verified'] == 1 and int(tor['votes']) > 0

setattr(torrentProvider.torrentProvider,'connect_kickass',connect_kickass)
setattr(torrentProvider.torrentProvider,'test_kickass',test_kickass)
setattr(torrentProvider.torrentProvider,'search_kickass',search_kickass)
setattr(torrentProvider.torrentProvider,'download_kickass',download_kickass)
setattr(torrentProvider.torrentProvider,'filter_kickass',filter_kickass)
setattr(torrentProvider.torrentProvider,'select_kickass',select_kickass)
