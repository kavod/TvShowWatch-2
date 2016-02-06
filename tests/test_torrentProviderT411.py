#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import torrentProvider
import os
import json
import logging
import httpretty
torrentProvider.loadProviders()

DEBUG=False

httpretty_urls = [
	("https://api.t411.in/auth",'tests/httpretty_t411_auth.json'),
	("https://api.t411.in/users/profile/12345678",'tests/httpretty_t411_auth.json'),
	("https://api.t411.in/torrents/search/home",'tests/httpretty_t411_search_home.json'),
	("https://api.t411.in/torrents/download/4711811",'tests/httpretty_t411_download.torrent'),
	]

msg = ''
loginFile = 'loginT411.json'
try:
	with open(os.path.dirname(os.path.abspath(__file__)) + '/' + loginFile) as data_file:    
		login = json.load(data_file)
except:
	msg=loginFile +" file in \"" + os.path.dirname(os.path.abspath(__file__)) + '" directory is expected with following content:\n{"username":"your_username","password":"your_password"}'
	
class TestTorrentProviderT411(unittest.TestCase):
	@httpretty.activate
	def setUp(self):
		global msg
		global login
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.assertEqual(msg,'',msg)
		self.torProv = torrentProvider.torrentProvider('t411',login,verbosity=DEBUG)
		
	def test_creation(self):
		self.assertIsInstance(self.torProv,torrentProvider.torrentProvider)
		
	@httpretty.activate
	def test_connect(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		self.torProv.connect()
		self.assertNotEqual(self.torProv.token,'ok')
		
	@httpretty.activate
	def test_test(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		self.torProv.connect()
		result = self.torProv.test()
		self.assertEqual(result,True)
		
	@httpretty.activate
	def test_search(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		self.torProv.connect()
		result = self.torProv.search('home')
		self.assertIsInstance(result,list)
		self.assertEqual(len(result),2)
		
	"""
	Unrelevant. Filter is done into the seach method
	@httpretty.activate
	def test_search_filter(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		self.torProv.connect()
		result = self.torProv.search('home')
		self.assertIsInstance(result,list)
		self.assertGreater(len(result),0)
		self.assertGreaterEqual(len(result),len(filter(self.torProv.filter,result)))"""
		
	@httpretty.activate
	def test_download(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		self.torProv.connect()
		result = self.torProv.search('home')
		result = self.torProv.select_torrent(result)
		tmpFile = self.torProv.download(result['id'])
		self.assertTrue(os.path.isfile(tmpFile))
		self.assertGreater(os.path.getsize(tmpFile),1000)
		os.remove(tmpFile)
		
	@httpretty.activate
	def test_select(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		self.torProv.connect()
		result = self.torProv.search('home')
		result = self.torProv.select_torrent(result)
		self.assertIsInstance(result,dict)
		self.assertIn(u'id',result.keys())
