#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import torrentSearch

class TestTorrentProviderKickAss(unittest.TestCase):
	def setUp(self):
		self.ts = torrentSearch.torrentSearch()
		self.configFile1 = "tests/torrentSearch1.json"
		self.conf1 = {u'keywords': [u'720p'], u'providers': [{u'id': u'kickass'}]}
		
	def test_creation(self):
		self.assertIsInstance(self.ts,torrentSearch.torrentSearch)
		
	def test_loadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile1))
		self.ts.loadConfig(self.configFile1)
		self.assertEqual(self.ts.conf.getValue(),self.conf1)
		
	def test_loadConfig_unexisted_file(self):
		tmpfile = unicode(tempfile.mkstemp('.conf')[1])
		os.remove(tmpfile)
		self.assertFalse(os.path.isfile(tmpfile))
		self.ts.loadConfig(tmpfile)
		self.assertTrue(os.path.isfile(tmpfile))
		os.remove(tmpfile)
		
	def test_displayConf(self):
		self.test_loadConfig()
		
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
