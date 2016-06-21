#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import torrentProvider
import httpretty

class TestTorrentProvider(unittest.TestCase):
	def setUp(self):
		httpretty.httpretty.allow_net_connect = False
		self.torProv = torrentProvider.torrentProvider('none',[])

	@httpretty.activate
	def test_creation(self):
		self.assertIsInstance(self.torProv,torrentProvider.torrentProvider)

	@httpretty.activate
	def test_connect(self):
		self.torProv.connect()
		self.assertEqual(self.torProv.token,'ok')
		
	@httpretty.activate
	def test_test(self):
		self.assertEqual(self.torProv.test(),True)

	@httpretty.activate
	def test_search(self):
		self.assertEqual(self.torProv.search('linux'),[])

	@httpretty.activate
	def test_download(self):
		self.assertEqual(self.torProv.download('linux'),False)

	@httpretty.activate
	def test_select(self):
		self.torProv.connect()
		self.assertEqual(self.torProv.select_torrent(['niouf','niorf']),'niouf')
