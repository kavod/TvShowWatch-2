#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import Downloader

class ConfTest(unittest.TestCase):
	def __init__(self,methodName='runTest',confFile=None):
		if confFile is None:
			Exception("Please indicate a configuration file")
		self.confFile = confFile
		super(ConfTest, self).__init__(methodName)

	def setUp(self):
		self.downloader = Downloader.Downloader(
			"downloader",
			dataFile=self.confFile,
			verbosity=False
		)

	def test_configFile(self):
		"""Is configurations files exists?"""
		pass

	def test_connect(self):
		"""Testing connection to torrent client"""
		if self.downloader['client'] != 'none':
			self.downloader.connect()
		else:
			unittest.skip("No torrent client setup".encode('utf8'))

	def test_folder_writable(self):
		"""Testing destination folder is writable"""
		if not self.downloader['deleteAfter']:
			self.assertTrue(os.access(self.downloader['torrentFolder'], os.W_OK))
		else:
			unittest.skip("Torrents are not stored".encode('utf8'))
