#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import torrentProvider
import os
import logging
import wwwoman
torrentProvider.loadProviders()

DEBUG=False

class TestTorrentProviderKickAss(unittest.TestCase):
	def setUp(self):
		wwwoman.wwwomanScenario.scenario_path = "tests/wwwoman/scenario"
		self.torProv = torrentProvider.torrentProvider('kat',None,verbosity=DEBUG)

	def test_creation(self):
		self.assertIsInstance(self.torProv,torrentProvider.torrentProvider)

	@wwwoman.register_scenario("kat_success.json")
	def test_connect(self):
		self.torProv.connect()
		self.assertNotEqual(self.torProv.token,'ok')

	@wwwoman.register_scenario("kat_success.json")
	def test_test(self):
		self.torProv.connect()
		result = self.torProv.test()
		self.assertEqual(result,True)

	@wwwoman.register_scenario("kat_success.json")
	def test_search(self):
		self.torProv.connect()
		result = self.torProv.search('home')
		self.assertIsInstance(result,list)
		self.assertGreater(len(result),0)

	@wwwoman.register_scenario("kat_success.json")
	def test_download(self):
		self.torProv.connect()
		result = self.torProv.search('home')
		result = self.torProv.select_torrent(result)
		tmpFile = self.torProv.download(result['id'])
		self.assertTrue(os.path.isfile(tmpFile))
		self.assertGreater(os.path.getsize(tmpFile),500)
		os.remove(tmpFile)

	@wwwoman.register_scenario("kat_success.json")
	def test_select(self):
		self.torProv.connect()
		result = self.torProv.search('home')
		result = self.torProv.select_torrent(result)
		self.assertIsInstance(result,dict)
		self.assertIn(u'id',result.keys())
		self.assertEqual(result['id'],"https://torcache.net/torrent/F261769DEEF448D86B23A8A0F2CFDEF0F64113C9.torrent?title=[kat.cr]home.is.a.2009.documentary.by.yann.arthus.bertrand.flv.en")
