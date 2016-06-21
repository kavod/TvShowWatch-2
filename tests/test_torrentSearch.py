#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import json
import torrentProvider
import torrentSearch
import logging
import httpretty
import wwwoman

DEBUG=False

T411_URL = (item for item in torrentProvider.TRACKER_CONF if item["id"] == "t411").next()['url']

class TestTorrentSearch(unittest.TestCase):
	def setUp(self):
		wwwoman.wwwomanScenario.scenario_path = "tests/wwwoman/scenario"
		self.ts = torrentSearch.torrentSearch(id="torrentSearch",verbosity=DEBUG)
		self.configFile2 = "tests/torrentSearch2.json"
		self.conf1 = {u'keywords': [u'720p'], u'providers': [{u'provider_type': u'kat',"keywords":["lang_id:2 verified:1"]}]}
		self.conf1['providers'].insert(0,{'provider_type':'t411','authentification':{"username":"your_username","password":"your_password"}})
		self.conf2 = dict(self.conf1)
		self.conf2['keywords'] = []

	def test_creation(self):
		self.assertIsInstance(self.ts,torrentSearch.torrentSearch)

	def test_loadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile2))
		self.ts.loadConfig(self.configFile2)
		self.assertEqual(self.ts.getValue(hidePassword=False),self.conf1)

	def test_loadConfig_unexisted_file(self):
		tmpfile = unicode(tempfile.mkstemp('.conf')[1])
		os.remove(tmpfile)
		self.assertFalse(os.path.isfile(tmpfile))
		self.ts.loadConfig(tmpfile)
		self.assertTrue(os.path.isfile(tmpfile))
		with open(tmpfile) as data_file:
			data = json.load(data_file)
		self.assertEqual(data,{"torrentSearch":{}})
		os.remove(tmpfile)

	@wwwoman.register_scenario("tp_all_success.json")
	def test_search(self):
		self.test_loadConfig()
		tor = self.ts.search("home")
		self.assertIsInstance(tor,dict)

	@wwwoman.register_scenario("tp_all_success.json")
	def test_download(self):
		self.test_loadConfig()
		tor = self.ts.search("home")
		tmpFile = self.ts.download(tor)
		self.assertTrue(os.path.isfile(tmpFile))
		os.remove(tmpFile)

	@wwwoman.register_scenario("tp_all_success.json")
	def test_search_wo_global_keyword(self):
		self.ts.data = self.conf2
		tor = self.ts.search("home")
		self.assertTrue(httpretty.has_request())
		self.assertEqual(httpretty.last_request().path,"/torrents/search/home")
