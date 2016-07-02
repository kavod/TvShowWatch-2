#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import torrentSearch

class ConfTest(unittest.TestCase):
	def __init__(self,methodName='runTest',confFile=None):
		if confFile is None:
			Exception("Please indicate a configuration file")
		self.confFile = confFile
		super(ConfTest, self).__init__(methodName)

	def setUp(self):
		self.ts = torrentSearch.torrentSearch(
			"torrentSearch",
			dataFile=self.confFile,
			verbosity=False
		)

	def test_configFile(self):
		"""Is configurations files exists?"""
		pass

	def test_connect_t411(self):
		"""Testing connection to T411"""
		if any('t411' == providers['provider_type'] for providers in self.ts['providers']):
			self.ts.connect_provider('t411')
			self.ts.test()
		else:
			unittest.skip("T411 is not setup".encode('utf8'))

	def test_connect_kat(self):
		"""Testing connection to KickAssTorrent"""
		if any('kat' == providers['provider_type'] for providers in self.ts['providers']):
			self.ts.connect_provider('kat')
			self.ts.test()
		else:
			unittest.skip("KickAssTorrent is not setup".encode('utf8'))
