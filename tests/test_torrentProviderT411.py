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
		self.assertIsInstance(self.torProv.search('linux'),list)
		self.assertGreater(len(self.torProv.search('linux')),0)
		
	def test_download(self):
		self.torProv.connect()
		result = self.torProv.search('linux')
		result = self.torProv.select_torrent(result)
		self.assertEqual(self.torProv.download(result['id']),'file:///tmp/file.torrent')
		self.assertGreater(os.path.getsize('/tmp/file.torrent'),1000)
		
	def test_select(self):
		self.torProv.connect()
		result = self.torProv.search('linux')
		result = self.torProv.select_torrent(result)
		self.assertIsInstance(result,dict)
		self.assertIn(u'id',result.keys())
