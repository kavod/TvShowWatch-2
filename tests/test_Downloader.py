#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import shutil
import json
import Downloader
import httpretty
import logging

DEBUG=False

httpretty_urls = [
	("http://localhost:9091/transmission/rpc",'tests/httpretty_transmission_add_torrent.json'),
	]

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
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.assertIsInstance(self.d,Downloader.Downloader)
		
	@httpretty.activate
	def test_loadConfig(self):
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])
		self.assertTrue(os.path.isfile(self.configFile1))
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile1)
		
	@httpretty.activate
	def test_loadConfig_with_path(self):
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])
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
		self.assertEqual(data,{"downloader":{}})
		os.remove(tmpfile)
		
	@httpretty.activate
	def test_add_torrent_transmission(self):
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                            ])
		if self.testTransmission:
			self.d = Downloader.Downloader(verbosity=DEBUG)
			self.d.loadConfig(self.configFileTransmission)
			logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
			if self.d.getValue()['client'] is not None:
				filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')
			
				tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
				os.remove(tmpfile)
				shutil.copyfile(filename, tmpfile)
			
				id = self.d.add_torrent(tmpfile,delTorrent=True)
				self.assertEqual(id,"3")
				self.assertFalse(os.path.isfile(tmpfile))
				return id
			
	@httpretty.activate
	def test_get_status_transmission(self):
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])
		if self.testTransmission:
			self.d = Downloader.Downloader()
			self.d.loadConfig(self.configFileTransmission)
			if self.d.data['client'] is not None:
				filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')
			
				tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
				os.remove(tmpfile)
				shutil.copyfile(filename, tmpfile)
			
				id = self.d.add_torrent(tmpfile,delTorrent=True)
				self.assertEqual(id,"3")
				self.assertFalse(os.path.isfile(tmpfile))
			status = self.d.get_status(id)
			self.assertIn(status,['check pending', 'checking', 'downloading', 'seeding'])
		
	@httpretty.activate	
	def test_get_files_transmission(self):
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])
		if self.testTransmission:
			self.d = Downloader.Downloader(verbosity=DEBUG)
			self.d.loadConfig(self.configFileTransmission)
			if self.d.data['client'] is not None:
				filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')
			
				tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
				os.remove(tmpfile)
				shutil.copyfile(filename, tmpfile)
			
				id = self.d.add_torrent(tmpfile,delTorrent=True)
				self.assertEqual(id,"3")
				self.assertFalse(os.path.isfile(tmpfile))
			files = self.d.get_files(id)
			self.assertEquals(files,['file1.txt', 'file2.tgz', 'foo/file4.txt'])
		
		
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
