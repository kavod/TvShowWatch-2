#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import json
import torrentSearch
import logging
import httpretty

DEBUG=False

httpretty_urls = [
	("https://api.t411.in/auth",'tests/httpretty_t411_auth.json'),
	("https://api.t411.in/users/profile/12345678",'tests/httpretty_t411_auth.json'),
	("https://api.t411.in/torrents/search/home%20720p",'tests/httpretty_t411_search_home.json'),
	("https://api.t411.in/torrents/download/4711811",'tests/httpretty_t411_download.torrent'),
	("https://kat.cr/json.php",'tests/httpretty_kat_search_home.json'),
	("https://torcache.net/torrent/F261769DEEF448D86B23A8A0F2CFDEF0F64113C9.torrent",'tests/httpretty_kat_download_home.magnet'),
	]
	
class TestTorrentSearch(unittest.TestCase):
	def setUp(self):
		self.ts = torrentSearch.torrentSearch(verbosity=DEBUG)
		self.configFile1 = "tests/torrentSearch1.json"
		self.conf1 = {u'keywords': [u'720p'], u'providers': [{u'id': u'kickass',"keywords":["lang_id:2 verified:1"]}]}
		self.conf1['providers'].insert(0,{'id':'t411','config':{"username":"your_username","password":"your_password"}})
		
	def test_creation(self):
		self.assertIsInstance(self.ts,torrentSearch.torrentSearch)
		
	def test_loadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile1))
		self.ts.loadConfig(self.configFile1)
		self.ts.conf['providers'].insert(0,{'id':'t411','config':{"username":"your_username","password":"your_password"}})
		self.assertEqual(self.ts.conf.getValue(hidePasswords=False),self.conf1)
		
	def test_loadConfig_with_path(self):
		with open(self.configFile1) as data_file:    
			data = json.load(data_file)
			
		tmpfile = unicode(tempfile.mkstemp('.conf')[1])
		with open(tmpfile, 'w') as outfile:
			json.dump({'torrentSearch':data}, outfile)
			
		self.ts.loadConfig(tmpfile,path=['torrentSearch'])
		self.ts.conf['providers'].insert(0,{'id':'t411','config':{"username":"your_username","password":"your_password"}})
		self.assertEqual(self.ts.conf.getValue(hidePasswords=False),self.conf1)
		os.remove(tmpfile)
		
	def test_loadConfig_unexisted_file(self):
		tmpfile = unicode(tempfile.mkstemp('.conf')[1])
		os.remove(tmpfile)
		self.assertFalse(os.path.isfile(tmpfile))
		self.ts.loadConfig(tmpfile)
		self.assertTrue(os.path.isfile(tmpfile))
		with open(tmpfile) as data_file:    
			data = json.load(data_file)
		self.assertEqual(data,{})
		os.remove(tmpfile)
		
	def test_loadConfig_unexisted_file_with_path(self):
		tmpfile = unicode(tempfile.mkstemp('.conf')[1])
		os.remove(tmpfile)
		self.assertFalse(os.path.isfile(tmpfile))
		self.ts.loadConfig(tmpfile,path=['torrentSearch'])
		self.assertTrue(os.path.isfile(tmpfile))
		with open(tmpfile) as data_file:    
			data = json.load(data_file)
		self.assertEqual(data,{u'torrentSearch': {}})
		os.remove(tmpfile)
		
	"""def test_displayConf(self):
		self.test_loadConfig()
		self.ts.displayConf()"""
		
	@httpretty.activate
	def test_search(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		self.test_loadConfig()
		tor = self.ts.search("home")
		self.assertIsInstance(tor,dict)
		
	@httpretty.activate
	def test_download(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		self.test_loadConfig()
		tor = self.ts.search("home")
		tmpFile = self.ts.download(tor)
		self.assertTrue(os.path.isfile(tmpFile))
		os.remove(tmpFile)
		
	# Interactive tests
	"""def test_cliConf(self):
		tmpfile = unicode(tempfile.mkstemp('.conf')[1])
		os.remove(tmpfile)
		self.ts.loadConfig(tmpfile)
		self.ts.cliConf()
		"""
