#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import datetime
import json
import tempfile
import httpretty
import myTvDB
import tvShowSchedule
import Downloader
import torrentSearch
import Transferer
import shutil

httpretty_urls = [
	("http://thetvdb.com/api/GetSeries.php",'tests/httpretty_myTvDB1.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/en.xml",'tests/httpretty_myTvDB2.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/all/en.xml",'tests/httpretty_myTvDB3.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/en.xml",'tests/httpretty_myTvDB4.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/all/en.xml",'tests/httpretty_myTvDB5.xml'),
	("https://api.t411.in/auth",'tests/httpretty_t411_auth.json'),
	("https://api.t411.in/users/profile/12345678",'tests/httpretty_t411_auth.json'),
	("https://api.t411.in/torrents/search/home",'tests/httpretty_t411_search_home.json'),
	("https://api.t411.in/torrents/search/TvShow%201%20S01E01%20720p",'tests/httpretty_t411_search_not_found.json'),
	("https://api.t411.in/torrents/download/4711811",'tests/httpretty_t411_download.torrent'),
	("https://torcache.net/torrent/F261769DEEF448D86B23A8A0F2CFDEF0F64113C9.torrent",'tests/httpretty_kat_download_home.magnet'),
				]
DEBUG=False

class TestTvShowSchedule(unittest.TestCase):
	def setUp(self):
		self.downloader = Downloader.Downloader(verbosity=DEBUG)
		self.transferer = Transferer.Transferer(id="transferer",verbosity=DEBUG)
		self.configFileTransmission = "tests/downloaderTransmission.json"
		self.configFileTvShowSchedule = "tests/tvShowSchedule.json"
		self.testTransmission =  os.path.isfile(self.configFileTransmission)
		
		self.tmpdir1 = unicode(tempfile.mkdtemp())
		self.tmpdir2 = unicode(tempfile.mkdtemp())
		self.transfererData = {"source": {"path": self.tmpdir1, "protocol": "file"}, "destination": {"path": self.tmpdir2, "protocol": "file"}}
		
		self.ts = torrentSearch.torrentSearch(id="torrentSearch",dataFile="tests/torrentSearch2.json",verbosity=DEBUG)
		self.t = myTvDB.myTvDB(debug=DEBUG,cache=not DEBUG)
		
	def tearDown(self):
		shutil.rmtree(self.tmpdir1)
		shutil.rmtree(self.tmpdir2)
	
	def test_creation(self):
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=73739,title='Lost',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow['status'],0)
		
	@httpretty.activate
	def test_creation_from_MyTvDB(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		t = myTvDB.myTvDB()
		tvShow = tvShowSchedule.tvShowScheduleFromMyTvDB(t[123],verbosity=DEBUG)
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow['status'],0)
		
	@httpretty.activate
	def test_creation_from_id(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowScheduleFromId(123,verbosity=DEBUG)
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow['status'],0)
		
	@httpretty.activate
	def test_update_0_to_10(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,title='TvShow 2',season=1,episode=2,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],0)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],10)
		
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,title='TvShow 2',season=0,episode=0,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],10)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],10)
		
	@httpretty.activate
	def test_update_0_to_20(self): # Added to waiting for torrent availability
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])
        
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		self.downloader.loadConfig(self.configFileTransmission)
		
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,title='TvShow 1',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],0)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],20)
		
	@httpretty.activate
	def test_update_0_to_30(self): # Added to Download in progress
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                            ])
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		self.downloader.loadConfig(self.configFileTransmission)
		
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,title='TvShow 1',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],0)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],30)
		
	"""
	# No more relevant. A new added TvShow without episode indicated will schedule the pilot
	@httpretty.activate
	def test_update_0_to_90(self): # Added to TvShow Achieved
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,title='TvShow 1',season=0,episode=0,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],0)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],90)"""
		
	@httpretty.activate
	def test_update_10_to_20(self): # not broadcasted to waiting for torrent availability
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "https://api.t411.in/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,title='TvShow 2',season=1,episode=1,status=10,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],10)

		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],20)
		
	@httpretty.activate
	def test_update_10_to_30(self): # not broadcasted to Download in progress
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "https://api.t411.in/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                            ])
		
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		self.downloader.loadConfig(self.configFileTransmission)
		
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,title='TvShow 2',season=1,episode=1,status=10,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],10)
		
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],30)
		
	@httpretty.activate
	def test_update_20_to_30(self): # Waiting for torrent availability to Download in progress
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "https://api.t411.in/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                            ])
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		self.downloader.loadConfig(self.configFileTransmission)
		
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,title='TvShow 2',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		tvShow._set(status=20)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],30)
		
	@httpretty.activate
	def test_update_30_to_10(self):
		files = ['file1.txt','file2.tgz','foo/file4.txt']
	
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "https://api.t411.in/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)

		os.makedirs(self.tmpdir1+"/foo")
		for myFile in files:
			with open(self.tmpdir1+"/"+myFile, 'a'):
				os.utime(self.tmpdir1+"/"+myFile, None)
		self.downloader.loadConfig(self.configFileTransmission)
		self.transferer.addData(self.configFileTvShowSchedule)
		self.transferer.setValue(self.transfererData)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,title='TvShow 2',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		tvShow._set(status=30,downloader_id = 3)	
		for myFile in files:
			self.assertTrue(os.path.isfile(self.tmpdir1+"/"+myFile))
			self.assertFalse(os.path.isfile(self.tmpdir2+"/"+myFile))	
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		for myFile in files:
			self.assertFalse(os.path.isfile(self.tmpdir1+"/"+myFile))
			self.assertTrue(os.path.isfile(self.tmpdir2+"/"+myFile))
		self.assertEqual(tvShow['status'],10)
		
	@httpretty.activate
	def test_update_30_to_90(self):
		files = ['file1.txt','file2.tgz','foo/file4.txt']
	
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "https://api.t411.in/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)

		os.makedirs(self.tmpdir1+"/foo")
		for myFile in files:
			with open(self.tmpdir1+"/"+myFile, 'a'):
				os.utime(self.tmpdir1+"/"+myFile, None)
		self.downloader.loadConfig(self.configFileTransmission)
		self.transferer.addData(self.configFileTvShowSchedule)
		self.transferer.setValue(self.transfererData)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,title='TvShow 2',season=1,episode=2,status=0,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		tvShow._set(status=30,downloader_id = 3)	
		for myFile in files:
			self.assertTrue(os.path.isfile(self.tmpdir1+"/"+myFile))
			self.assertFalse(os.path.isfile(self.tmpdir2+"/"+myFile))	
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		for myFile in files:
			self.assertFalse(os.path.isfile(self.tmpdir1+"/"+myFile))
			self.assertTrue(os.path.isfile(self.tmpdir2+"/"+myFile))
		self.assertEqual(tvShow['status'],90)
	
	@httpretty.activate
	def test_update_90_to_10(self): # Achieved to watching
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,title='TvShow 2',season=0,episode=0,status=90,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],90)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],10)
		
	@httpretty.activate
	def test_update_90_to_90(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,title='TvShow 1',season=0,episode=0,status=90,nextUpdate=datetime.datetime.now(),verbosity=DEBUG)
		self.assertEqual(tvShow['status'],90)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],90)
