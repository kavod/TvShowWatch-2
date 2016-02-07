#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import torrentProvider
import os
import logging
import httpretty
torrentProvider.loadProviders()

DEBUG=False

httpretty_urls = [
	("https://kat.cr/json.php",'tests/httpretty_kat_search_home.json'),
	("https://torcache.net/torrent/F261769DEEF448D86B23A8A0F2CFDEF0F64113C9.torrent",'tests/httpretty_kat_download_home.magnet'),
	]

class TestTorrentProviderKickAss(unittest.TestCase):
	def setUp(self):
		self.torProv = torrentProvider.torrentProvider('kickass',None,verbosity=DEBUG)
		
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
		self.assertGreater(len(result),0)
		
	'''
	Unrelevant. Filter is done into the seach method
	def test_search_filter(self):
		self.torProv.connect()
		result = self.torProv.search('linux')
		self.assertIsInstance(result,list)
		self.assertGreater(len(result),0)
		self.assertGreaterEqual(len(result),len(filter(self.torProv.filter,result)))'''
		
	@httpretty.activate
	def test_download(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.torProv.connect()
		result = self.torProv.search('home')
		result = self.torProv.select_torrent(result)
		tmpFile = self.torProv.download(result['id'])
		self.assertTrue(os.path.isfile(tmpFile))
		self.assertGreater(os.path.getsize(tmpFile),500)
		os.remove(tmpFile)
		
	@httpretty.activate
	def test_select(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.torProv.connect()
		result = self.torProv.search('home')
		result = self.torProv.select_torrent(result)
		self.assertIsInstance(result,dict)
		self.assertIn(u'id',result.keys())
		self.assertEqual(result['id'],"https://torcache.net/torrent/F261769DEEF448D86B23A8A0F2CFDEF0F64113C9.torrent?title=[kat.cr]home.is.a.2009.documentary.by.yann.arthus.bertrand.flv.en")
