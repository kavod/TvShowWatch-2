#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import torrentProvider
import os
import json

msg = ''
loginFile = 'loginT411.json'
try:
	with open(os.path.dirname(os.path.abspath(__file__)) + '/' + loginFile) as data_file:    
		login = json.load(data_file)
except:
	msg=loginFile +" file in \"" + os.path.dirname(os.path.abspath(__file__)) + '" directory is expected with following content:\n{"username":"your_username","password":"your_password"}'
	
class TestTorrentProviderT411(unittest.TestCase):
	def setUp(self):
		global msg
		global login
		self.assertEqual(msg,'',msg)
		self.torProv = torrentProvider.torrentProvider('t411',login)
		
	def test_creation(self):
		self.assertIsInstance(self.torProv,torrentProvider.torrentProvider)
		
	def test_connect(self):
		self.torProv.connect()
		self.assertNotEqual(self.torProv.token,'ok')
		
	def test_test(self):
		self.torProv.connect()
		result = self.torProv.test()
		self.assertEqual(result,True)
		
	def test_search(self):
		self.torProv.connect()
		result = self.torProv.search('linux')
		self.assertIsInstance(result,list)
		self.assertGreater(len(result),0)
		
	def test_search_filter(self):
		self.torProv.connect()
		result = self.torProv.search('linux')
		self.assertIsInstance(result,list)
		self.assertGreater(len(result),0)
		self.assertGreaterEqual(len(result),len(filter(self.torProv.filter,result)))
		
	def test_download(self):
		self.torProv.connect()
		result = self.torProv.search('linux')
		result = self.torProv.select_torrent(result)
		tmpFile = self.torProv.download(result['id'])
		self.assertTrue(os.path.isfile(tmpFile))
		self.assertGreater(os.path.getsize(tmpFile),1000)
		os.remove(tmpFile)
		
	def test_select(self):
		self.torProv.connect()
		result = self.torProv.search('linux')
		result = self.torProv.select_torrent(result)
		self.assertIsInstance(result,dict)
		self.assertIn(u'id',result.keys())
