#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import torrentProvider

class TestTorrentProvider(unittest.TestCase):
	def setUp(self):
		self.torProv = torrentProvider.torrentProvider('none',[])
		
	def test_creation(self):
		self.assertIsInstance(self.torProv,torrentProvider.torrentProvider)
		
	def test_connect(self):
		self.torProv.connect()
		self.assertEqual(self.torProv.token,'ok')
		
	def test_test(self):
		self.assertEqual(self.torProv.test(),True)
		
	def test_search(self):
		self.assertEqual(self.torProv.search('linux'),[])
		
	def test_download(self):
		self.assertEqual(self.torProv.download('linux'),False)
		
	def test_select(self):
		self.torProv.connect()
		self.assertEqual(self.torProv.select_torrent(['niouf','niorf']),'niouf')
