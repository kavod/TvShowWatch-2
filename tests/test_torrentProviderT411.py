#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import torrentProvider
import os
import wwwoman
torrentProvider.loadProviders()

DEBUG=False

T411_URL = (item for item in torrentProvider.TRACKER_CONF if item["id"] == "t411").next()['url']

class TestTorrentProviderT411(unittest.TestCase):
	def setUp(self):
		wwwoman.wwwomanScenario.scenario_path = "tests/wwwoman/scenario"
		self.torProv = torrentProvider.torrentProvider('t411',{"username":"your_username","password":"your_password"},verbosity=DEBUG)

	def test_creation(self):
		self.assertIsInstance(self.torProv,torrentProvider.torrentProvider)

	@wwwoman.register_scenario("t411_success.json")
	def test_connect(self):
		self.torProv.connect()
		self.assertNotEqual(self.torProv.token,'ok')

	@wwwoman.register_scenario("t411_success.json")
	def test_test(self):
		self.torProv.connect()
		result = self.torProv.test()
		self.assertEqual(result,True)

	@wwwoman.register_scenario("t411_success.json")
	def test_search(self):
		self.torProv.connect()
		result = self.torProv.search('home')
		self.assertIsInstance(result,list)
		self.assertEqual(len(result),2)

	@wwwoman.register_scenario("t411_success.json")
	def test_download(self):
		self.torProv.connect()
		result = self.torProv.search('home')
		result = self.torProv.select_torrent(result)
		tmpFile = self.torProv.download(result['id'])
		self.assertTrue(os.path.isfile(tmpFile))
		self.assertGreater(os.path.getsize(tmpFile),1000)
		os.remove(tmpFile)

	@wwwoman.register_scenario("t411_success.json")
	def test_select(self):
		self.torProv.connect()
		result = self.torProv.search('home')
		result = self.torProv.select_torrent(result)
		self.assertIsInstance(result,dict)
		self.assertIn(u'id',result.keys())
