#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import json
import torrentSearch

t411LoginFile = os.path.dirname(os.path.abspath(__file__)) + '/loginT411.json'

class TestTorrentProviderKickAss(unittest.TestCase):
	def setUp(self):
		self.ts = torrentSearch.torrentSearch()
		self.configFile1 = "tests/torrentSearch1.json"
		self.conf1 = {u'keywords': [u'720p'], u'providers': [{u'id': u'kickass'}]}
		if os.path.isfile(t411LoginFile):
			with open(t411LoginFile) as data_file:    
				data = json.load(data_file)
			self.conf1['providers'].insert(0,{'id':'t411','config':data})
		
	def test_creation(self):
		self.assertIsInstance(self.ts,torrentSearch.torrentSearch)
		
	def test_loadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile1))
		self.ts.loadConfig(self.configFile1)
		if os.path.isfile(t411LoginFile):
			with open(t411LoginFile) as data_file:    
				data = json.load(data_file)
			self.ts.conf['providers'].insert(0,{'id':'t411','config':data})
		self.assertEqual(self.ts.conf.getValue(hidePasswords=False),self.conf1)
		
	def test_loadConfig_unexisted_file(self):
		tmpfile = unicode(tempfile.mkstemp('.conf')[1])
		os.remove(tmpfile)
		self.assertFalse(os.path.isfile(tmpfile))
		self.ts.loadConfig(tmpfile)
		self.assertTrue(os.path.isfile(tmpfile))
		os.remove(tmpfile)
		
	def test_displayConf(self):
		self.test_loadConfig()
		self.ts.displayConf()
		
	def test_search(self):
		self.test_loadConfig()
		tor = self.ts.search("home 2009")
		self.assertIsInstance(tor,dict)
		
	def test_download(self):
		self.test_loadConfig()
		tor = self.ts.search("home 2009")
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
