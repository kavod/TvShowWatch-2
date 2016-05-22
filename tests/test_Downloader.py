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
import LogTestCase

httpretty.HTTPretty.allow_net_connect = False

DEBUG=False

httpretty_urls = [
	("http://localhost:9091/transmission/rpc",'tests/httpretty_transmission_add_torrent.json'),
	]

class TestDownloader(LogTestCase.LogTestCase):
	def setUp(self):
		self.configFile1 = "tests/downloader1.json"
		self.conf1 = {"client":"transmission","transConf":{"address":"localhost","port":9091}}

		self.configFile2 = "tests/downloader2.json"
		self.conf2 = self.conf1

		self.configFile3 = "tests/downloader3.json"

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
	def test_synoloadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile3))
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)

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

		self.d = Downloader.Downloader(dataFile=tmpfile)
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
	def test_add_torrent_synology(self):
		httpretty.register_uri(httpretty.GET, "https://localhost:5001/webapi/auth.cgi",responses=[
                               httpretty.Response(body='{"data":{"sid":"ZexNvOGV.xh7kA4GEN01857"},"success":true}')
							   ])
   		httpretty.register_uri(httpretty.GET, "https://localhost:5001/webapi/DownloadStation/task.cgi",responses=[
			httpretty.Response(body='{"data":{"offeset":0,"tasks":[],"total":0},"success":true}'), # list
			httpretty.Response(body='{"data":{"offeset":0,"tasks":[],"total":0},"success":true}'), # list
			httpretty.Response(body='''{"data":{"offeset":0,"tasks":[{"id":"dbid_160","size":"0","status":"waiting","status_extra":null,
				"title":"tmpvgwQmq.torrent","type":"bt","username":"test"}],"total":1},"success":true}'''), # list
   							   ])
   		httpretty.register_uri(httpretty.POST, "https://localhost:5001/webapi/DownloadStation/task.cgi",responses=[
			httpretty.Response(body='{"success":true}'), # create
			])
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
		if self.d.getValue()['client'] is not None:
			filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

			tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
			os.remove(tmpfile)
			shutil.copyfile(filename, tmpfile)

			id = self.d.add_torrent(tmpfile,delTorrent=True)
			self.assertEqual(id,"dbid_160")
			self.assertFalse(os.path.isfile(tmpfile))

	@httpretty.activate
	def test_add_torrent_transmission_corrupt(self):
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent_corrupt.json','r').read()),
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

				with self.assertLogs(level='ERROR'):
					id = self.d.add_torrent(tmpfile,delTorrent=True)
				self.assertEqual(id,-1)
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
	def test_get_status_synology(self):
		httpretty.register_uri(httpretty.GET, "https://localhost:5001/webapi/auth.cgi",responses=[
                               httpretty.Response(body='{"data":{"sid":"ZexNvOGV.xh7kA4GEN01857"},"success":true}')
							   ])
   		httpretty.register_uri(httpretty.GET, "https://localhost:5001/webapi/DownloadStation/task.cgi",responses=[
			httpretty.Response(body='''{"data": {"total": 1, "tasks": [{"additional":{"detail":{"connected_leechers":0,
				"connected_seeders":1,"create_time":"1463927215","destination":"home/downloads","priority":"auto","total_peers":0,
				"uri":"tmpvgwQmq.torrent"},"file":[{"filename":"tracked_by_h33t_com.txt","priority":"normal","size":"185",
				"size_downloaded":"185"},{"filename":"Ubuntu.Linux.Toolbox-2nd.Edition.tgz","priority":"normal","size":"7010029",
				"size_downloaded":"4454125"},{"filename":"Torrent downloaded from AhaShare.com.txt","priority":"normal","size":"58",
				"size_downloaded":"58"},{"filename":"Torrent Downloaded From ExtraTorrent.cc.txt","priority":"normal","size":"352",
				"size_downloaded":"352"}],"transfer":{"size_downloaded":"4454720","size_uploaded":"0","speed_download":1172,
				"speed_upload":0}},"status": "downloading", "username": "test",	"status_extra": null,
				"title": "Ubuntu Linux Toolbox - 1000+ Commands for Ubuntu and Debian Power Users", "type": "bt", "id": "dbid_160",
				"size": "7010624"}], "offeset": 0}, "success": true}'''), # list
			httpretty.Response(body='''{"data": {"total": 1, "tasks": [{"additional":{"detail":{"connected_leechers":0,
				"connected_seeders":1,"create_time":"1463927215","destination":"home/downloads","priority":"auto","total_peers":0,
				"uri":"tmpvgwQmq.torrent"},"file":[{"filename":"tracked_by_h33t_com.txt","priority":"normal","size":"185",
				"size_downloaded":"185"},{"filename":"Ubuntu.Linux.Toolbox-2nd.Edition.tgz","priority":"normal","size":"7010029",
				"size_downloaded":"4454125"},{"filename":"Torrent downloaded from AhaShare.com.txt","priority":"normal","size":"58",
				"size_downloaded":"58"},{"filename":"Torrent Downloaded From ExtraTorrent.cc.txt","priority":"normal","size":"352",
				"size_downloaded":"352"}],"transfer":{"size_downloaded":"4454720","size_uploaded":"0","speed_download":1172,
				"speed_upload":0}},"status": "downloading", "username": "test",	"status_extra": null,
				"title": "Ubuntu Linux Toolbox - 1000+ Commands for Ubuntu and Debian Power Users", "type": "bt", "id": "dbid_160",
				"size": "7010624"}], "offeset": 0}, "success": true}'''), # list
				])
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
		if self.d.getValue()['client'] is not None:
			filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

			tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
			os.remove(tmpfile)
			shutil.copyfile(filename, tmpfile)

			id = self.d.add_torrent(tmpfile,delTorrent=True)
			self.assertEqual(id,"dbid_160")
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

	@httpretty.activate
	def test_get_files_synology(self):
		httpretty.register_uri(httpretty.GET, "https://localhost:5001/webapi/auth.cgi",responses=[
                               httpretty.Response(body='{"data":{"sid":"ZexNvOGV.xh7kA4GEN01857"},"success":true}')
							   ])
   		httpretty.register_uri(httpretty.GET, "https://localhost:5001/webapi/DownloadStation/task.cgi",responses=[
			httpretty.Response(body='''{"data": {"total": 1, "tasks": [{"additional":{"detail":{"connected_leechers":0,
				"connected_seeders":1,"create_time":"1463927215","destination":"home/downloads","priority":"auto","total_peers":0,
				"uri":"tmpvgwQmq.torrent"},"file":[{"filename":"tracked_by_h33t_com.txt","priority":"normal","size":"185",
				"size_downloaded":"185"},{"filename":"Ubuntu.Linux.Toolbox-2nd.Edition.tgz","priority":"normal","size":"7010029",
				"size_downloaded":"4454125"},{"filename":"Torrent downloaded from AhaShare.com.txt","priority":"normal","size":"58",
				"size_downloaded":"58"},{"filename":"Torrent Downloaded From ExtraTorrent.cc.txt","priority":"normal","size":"352",
				"size_downloaded":"352"}],"transfer":{"size_downloaded":"4454720","size_uploaded":"0","speed_download":1172,
				"speed_upload":0}},"status": "downloading", "username": "test",	"status_extra": null,
				"title": "Ubuntu Linux Toolbox - 1000+ Commands for Ubuntu and Debian Power Users", "type": "bt", "id": "dbid_160",
				"size": "7010624"}], "offeset": 0}, "success": true}'''), # list
			httpretty.Response(body='''{"data": {"total": 1, "tasks": [{"additional":{"detail":{"connected_leechers":0,
				"connected_seeders":1,"create_time":"1463927215","destination":"home/downloads","priority":"auto","total_peers":0,
				"uri":"tmpvgwQmq.torrent"},"file":[{"filename":"tracked_by_h33t_com.txt","priority":"normal","size":"185",
				"size_downloaded":"185"},{"filename":"Ubuntu.Linux.Toolbox-2nd.Edition.tgz","priority":"normal","size":"7010029",
				"size_downloaded":"4454125"},{"filename":"Torrent downloaded from AhaShare.com.txt","priority":"normal","size":"58",
				"size_downloaded":"58"},{"filename":"Torrent Downloaded From ExtraTorrent.cc.txt","priority":"normal","size":"352",
				"size_downloaded":"352"}],"transfer":{"size_downloaded":"4454720","size_uploaded":"0","speed_download":1172,
				"speed_upload":0}},"status": "downloading", "username": "test",	"status_extra": null,
				"title": "Ubuntu Linux Toolbox - 1000+ Commands for Ubuntu and Debian Power Users", "type": "bt", "id": "dbid_160",
				"size": "7010624"}], "offeset": 0}, "success": true}'''), # list
				])
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
		if self.d.getValue()['client'] is not None:
			filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

			tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
			os.remove(tmpfile)
			shutil.copyfile(filename, tmpfile)

			id = self.d.add_torrent(tmpfile,delTorrent=True)
			self.assertEqual(id,"dbid_160")
			self.assertFalse(os.path.isfile(tmpfile))

			files = self.d.get_files(id)
			self.assertEquals(files,[
				'tracked_by_h33t_com.txt',
				'Ubuntu.Linux.Toolbox-2nd.Edition.tgz',
				'Torrent downloaded from AhaShare.com.txt',
				'Torrent Downloaded From ExtraTorrent.cc.txt'
			])

	@httpretty.activate
	def test_get_progression_transmission(self):
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
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
			progression = self.d.get_progression(id)
			self.assertEquals(progression,75)


	@httpretty.activate
	def test_get_progression_synology(self):
		httpretty.register_uri(httpretty.GET, "https://localhost:5001/webapi/auth.cgi",responses=[
                               httpretty.Response(body='{"data":{"sid":"ZexNvOGV.xh7kA4GEN01857"},"success":true}')
							   ])
   		httpretty.register_uri(httpretty.GET, "https://localhost:5001/webapi/DownloadStation/task.cgi",responses=[
			httpretty.Response(body='''{"data": {"total": 1, "tasks": [{"additional":{"detail":{"connected_leechers":0,
				"connected_seeders":1,"create_time":"1463927215","destination":"home/downloads","priority":"auto","total_peers":0,
				"uri":"tmpvgwQmq.torrent"},"file":[{"filename":"tracked_by_h33t_com.txt","priority":"normal","size":"185",
				"size_downloaded":"185"},{"filename":"Ubuntu.Linux.Toolbox-2nd.Edition.tgz","priority":"normal","size":"7010029",
				"size_downloaded":"4454125"},{"filename":"Torrent downloaded from AhaShare.com.txt","priority":"normal","size":"58",
				"size_downloaded":"58"},{"filename":"Torrent Downloaded From ExtraTorrent.cc.txt","priority":"normal","size":"352",
				"size_downloaded":"352"}],"transfer":{"size_downloaded":"4454720","size_uploaded":"0","speed_download":1172,
				"speed_upload":0}},"status": "downloading", "username": "test",	"status_extra": null,
				"title": "Ubuntu Linux Toolbox - 1000+ Commands for Ubuntu and Debian Power Users", "type": "bt", "id": "dbid_160",
				"size": "7010624"}], "offeset": 0}, "success": true}'''), # list
			httpretty.Response(body='''{"data": {"total": 1, "tasks": [{"additional":{"detail":{"connected_leechers":0,
				"connected_seeders":1,"create_time":"1463927215","destination":"home/downloads","priority":"auto","total_peers":0,
				"uri":"tmpvgwQmq.torrent"},"file":[{"filename":"tracked_by_h33t_com.txt","priority":"normal","size":"185",
				"size_downloaded":"185"},{"filename":"Ubuntu.Linux.Toolbox-2nd.Edition.tgz","priority":"normal","size":"7010029",
				"size_downloaded":"4454125"},{"filename":"Torrent downloaded from AhaShare.com.txt","priority":"normal","size":"58",
				"size_downloaded":"58"},{"filename":"Torrent Downloaded From ExtraTorrent.cc.txt","priority":"normal","size":"352",
				"size_downloaded":"352"}],"transfer":{"size_downloaded":"4454720","size_uploaded":"0","speed_download":1172,
				"speed_upload":0}},"status": "downloading", "username": "test",	"status_extra": null,
				"title": "Ubuntu Linux Toolbox - 1000+ Commands for Ubuntu and Debian Power Users", "type": "bt", "id": "dbid_160",
				"size": "7010624"}], "offeset": 0}, "success": true}'''), # list
				])
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
		if self.d.getValue()['client'] is not None:
			filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

			tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
			os.remove(tmpfile)
			shutil.copyfile(filename, tmpfile)

			id = self.d.add_torrent(tmpfile,delTorrent=True)
			self.assertEqual(id,"dbid_160")
			self.assertFalse(os.path.isfile(tmpfile))

			progression = self.d.get_progression(id)
			self.assertEquals(progression,63)

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
