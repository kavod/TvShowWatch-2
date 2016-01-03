#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import shutil
import json
import Downloader

class TestDownloader(unittest.TestCase):
	def setUp(self):
		self.configFile1 = "tests/downloader1.json"
		self.conf1 = {"client":"transmission","transConf":{"address":"localhost","port":9091}}
		
		self.configFile2 = "tests/downloader2.json"
		self.conf2 = self.conf1
		
		self.configFileTransmission = "tests/downloaderTransmission.json"
		self.testTransmission =  os.path.isfile(self.configFileTransmission)
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		
	def test_creation(self):
		self.d = Downloader.Downloader()
		self.assertIsInstance(self.d,Downloader.Downloader)
		
	def test_loadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile1))
		self.d = Downloader.Downloader()
		self.d.loadConfig(self.configFile1)
		
	def test_loadConfig_with_path(self):
		self.assertTrue(os.path.isfile(self.configFile2))
		self.d = Downloader.Downloader()
		self.d.loadConfig(self.configFile2,path=['downloader'])
		
	def test_loadConfig_unexisted_file(self):
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		self.assertFalse(os.path.isfile(tmpfile))
		
		self.d = Downloader.Downloader()
		self.d.loadConfig(tmpfile)
		
		self.assertTrue(os.path.isfile(tmpfile))
		with open(tmpfile) as data_file:    
			data = json.load(data_file)
		self.assertEqual(data,{"client":"none"})
		os.remove(tmpfile)
		
	def test_add_torrent_transmission(self):
		if self.testTransmission:
			self.d = Downloader.Downloader()
			self.d.loadConfig(self.configFileTransmission)
			if self.d.conf['client'] is not None:
				filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')
			
				tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
				os.remove(tmpfile)
				shutil.copyfile(filename, tmpfile)
			
				id = self.d.add_torrent(tmpfile,delTorrent=True)
				self.assertIsInstance(id,unicode)
				self.assertFalse(os.path.isfile(tmpfile))
				return id
			
	def test_get_status_transmission(self):
		if self.testTransmission:
			id = self.test_add_torrent_transmission()
			status = self.d.get_status(id)
			self.assertIn(status,['check pending', 'checking', 'downloading', 'seeding'])
		
	#Interactives tests
	"""def test_cliConf(self):
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		self.d = Downloader.Downloader()
		self.d.loadConfig(tmpfile)
		self.d.cliConf()
		
	def test_displayConf(self):
		self.d = Downloader.Downloader()
		self.d.loadConfig(self.configFile1)
		self.d.displayConf()"""
