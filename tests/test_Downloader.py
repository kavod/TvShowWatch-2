#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import shutil
import json
import Downloader
import logging
import LogTestCase
import wwwoman

DEBUG=False

class TestDownloader(LogTestCase.LogTestCase):
	def setUp(self):
		wwwoman.wwwomanScenario.scenario_path = "tests/wwwoman/scenario"
		wwwoman.wwwoman.allow_net_connect = False

		self.configFile1 = "tests/downloader1.json"
		self.conf1 = {"client":"transmission","transConf":{"address":"localhost","port":9091}}

		self.configFile2 = "tests/downloader2.json"
		self.conf2 = self.conf1

		self.configFile3 = "tests/downloader3.json"

		self.configFileTransmission = "tests/downloaderTransmission.json"
		self.configFileNone = "tests/downloaderNone.json"
		self.testTransmission =  os.path.isfile(self.configFileTransmission)

	def test_creation(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.assertIsInstance(self.d,Downloader.Downloader)

	def test_loadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile1))
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile1)

	def test_synoloadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile3))
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)

	def test_loadConfig_with_path(self):
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

	@wwwoman.register_scenario("transmission_sess_get_add.json")
	def test_add_torrent_transmission(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFileTransmission)
		logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
		self.assertIsNotNone(self.d.getValue()['client'])
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		id = self.d.add_torrent(tmpfile)
		self.assertEqual(id,"3")
		self.assertFalse(os.path.isfile(tmpfile))
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),3)

	@wwwoman.register_scenario("synology.json")
	def test_add_torrent_synology(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		id = self.d.add_torrent(tmpfile)
		self.assertEqual(id,"dbid_160")
		self.assertFalse(os.path.isfile(tmpfile))

	def test_add_torrent_none(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFileNone)
		self.d['torrentFolder'] = unicode(tempfile.mkdtemp())
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		destfile = "{0}/{1}".format(self.d['torrentFolder'],os.path.basename(tmpfile))
		shutil.copyfile(filename, tmpfile)

		id = self.d.add_torrent(tmpfile)
		self.assertEqual(id,"")
		self.assertFalse(os.path.isfile(tmpfile))
		self.assertTrue(os.path.isfile(destfile))
		os.remove(destfile)

	@wwwoman.register_scenario("transmission_sess_get_add_corrupt.json")
	def test_add_torrent_transmission_corrupt(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFileTransmission)
		self.assertIsNotNone(self.d.data['client'])
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		with self.assertRaises(Downloader.DownloaderCorruptedTorrent):
			with self.assertLogs(logger=self.d.logger,level='ERROR'):
				id = self.d.add_torrent(tmpfile)
		os.remove(tmpfile)
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),3)

	@wwwoman.register_scenario("transmission_sess_get_add.json")
	def test_get_status_transmission(self):
		self.d = Downloader.Downloader()
		self.d.loadConfig(self.configFileTransmission)
		self.assertIsNotNone(self.d.data['client'])
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		id = self.d.add_torrent(tmpfile,delTorrent=True)
		self.assertEqual(id,"3")
		self.assertFalse(os.path.isfile(tmpfile))
		status = self.d.get_status(id)
		self.assertIn(status,['check pending', 'checking', 'downloading', 'seeding'])
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),4)

	@wwwoman.register_scenario("synology_get_progression.json")
	def test_get_status_synology(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
		self.assertIsNotNone(self.d.data['client'])
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		id = self.d.add_torrent(tmpfile,delTorrent=True)
		self.assertEqual(id,"dbid_160")
		self.assertFalse(os.path.isfile(tmpfile))

		status = self.d.get_status(id)
		self.assertIn(status,['check pending', 'checking', 'downloading', 'seeding'])
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),4)

	@wwwoman.register(method="GET", uri="https://localhost:5001/webapi/auth.cgi",status=500)
	def test_synology_connectionError(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
		self.assertIsNotNone(self.d.data['client'])
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		with self.assertRaises(Downloader.DownloaderConnectionError):
			with self.assertLogs(logger=self.d.logger,level='ERROR'):
				id = self.d.add_torrent(tmpfile,delTorrent=True)
		os.remove(tmpfile)
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),1)

	@wwwoman.register_scenario("transmission_sess_get_add.json")
	def test_get_files_transmission(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFileTransmission)
		self.assertIsNotNone(self.d.data['client'])
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		id = self.d.add_torrent(tmpfile,delTorrent=True)
		self.assertEqual(id,"3")
		self.assertFalse(os.path.isfile(tmpfile))
		files = self.d.get_files(id)
		self.assertEquals(files,['file1.txt', 'file2.tgz', 'foo/file4.txt'])
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),4)

	@wwwoman.register_scenario("synology_get_progression.json")
	def test_get_files_synology(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		self.d.logger.debug("[Downloader] Data:\n".format(unicode(self.d)))
		self.assertIsNotNone(self.d.data['client'])
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

	@wwwoman.register_scenario("transmission_sess_getDl_add_getDl.json")
	def test_get_progression_transmission(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFileTransmission)
		self.assertIsNotNone(self.d.data['client'])
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		id = self.d.add_torrent(tmpfile,delTorrent=True)
		self.assertEqual(id,"3")
		self.assertFalse(os.path.isfile(tmpfile))
		progression = self.d.get_progression(id)
		self.assertEquals(progression,75)
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),4)


	@wwwoman.register_scenario("synology_get_progression.json")
	def test_get_progression_synology(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		logging.debug("[Downloader] Data:\n".format(unicode(self.d)))
		self.assertIsNotNone(self.d.data['client'])
		filename = "{0}/{1}".format(os.path.dirname(os.path.abspath(__file__)),'test.torrent')

		tmpfile = unicode(tempfile.mkstemp('.torrent')[1])
		os.remove(tmpfile)
		shutil.copyfile(filename, tmpfile)

		id = self.d.add_torrent(tmpfile,delTorrent=True)
		self.assertEqual(id,"dbid_160")
		self.assertFalse(os.path.isfile(tmpfile))

		progression = self.d.get_progression(id)
		self.assertEquals(progression,63)

	@wwwoman.register_scenario("transmission_sess_getDl_add_getDl.json")
	def test_transmission_start_fail(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFileTransmission)

		with self.assertLogs(logger=self.d.logger,level='ERROR'):
			with self.assertRaises(Downloader.DownloaderSlotNotExists):
				self.d.start_torrent(5)
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),2)

	@wwwoman.register_scenario("synology_start_failed.json")
	def test_synology_start_fail(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)

		with self.assertLogs(logger=self.d.logger,level='ERROR'):
			with self.assertRaises(Downloader.DownloaderSlotNotExists):
				self.d.start_torrent('dbid_161')

	@wwwoman.register_scenario("transmission_sess_getDl_success.json")
	def test_transmission_start_success(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFileTransmission)
		self.d.start_torrent(3)
		self.assertEqual(len(wwwoman.wwwoman.latest_requests),3)

	@wwwoman.register_scenario("synology_start_success.json")
	def test_synology_start_success(self):
		self.d = Downloader.Downloader(verbosity=DEBUG)
		self.d.loadConfig(self.configFile3)
		self.d.start_torrent('dbid_161')
