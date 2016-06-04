#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import time
import datetime
import json
import tempfile
import shutil
import httpretty
import mock
import LogTestCase
import myTvDB
import torrentProvider
import tvShowSchedule
import Downloader
import torrentSearch
import Transferer
import shutil

httpretty.HTTPretty.allow_net_connect = False

T411_URL = (item for item in torrentProvider.TRACKER_CONF if item["id"] == "t411").next()['url']

httpretty_urls = [
	("http://thetvdb.com/api/GetSeries.php",'tests/httpretty_myTvDB1.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/en.xml",'tests/httpretty_myTvDB2.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/all/en.xml",'tests/httpretty_myTvDB3.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/en.xml",'tests/httpretty_myTvDB4.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/all/en.xml",'tests/httpretty_myTvDB5.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/111/en.xml",'tests/httpretty_myTvDB8.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/111/all/en.xml",'tests/httpretty_myTvDB9.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/456/en.xml",'tests/httpretty_myTvDB4.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/456/all/en.xml",'tests/httpretty_myTvDB7.xml'),
	("http://thetvdb.com/banners/_cache/graphical/123-g4.jpg",'tests/image.jpg'),
	(T411_URL + "/auth",'tests/httpretty_t411_auth.json'),
	(T411_URL + "/users/profile/12345678",'tests/httpretty_t411_auth.json'),
	(T411_URL + "/torrents/search/home",'tests/httpretty_t411_search_home.json'),
	(T411_URL + "/torrents/search/TvShow%201%20S01E01%20720p",'tests/httpretty_t411_search_not_found.json'),
	(T411_URL + "/torrents/download/4711811",'tests/httpretty_t411_download.torrent'),
	("https://torcache.net/torrent/F261769DEEF448D86B23A8A0F2CFDEF0F64113C9.torrent",'tests/httpretty_kat_download_home.magnet'),
				]
DEBUG=False
DEBUG_TORRENT_SEARCH=DEBUG
DEBUG_TVSHOWSCHEDULE=DEBUG

class TestTvShowSchedule(LogTestCase.LogTestCase):
	@httpretty.activate
	def setUp(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.downloader = Downloader.Downloader(verbosity=DEBUG)
		self.transferer = Transferer.Transferer(id="transferer",verbosity=DEBUG)
		self.configFileTransmission = "tests/downloaderTransmission.json"
		self.configFileTvShowSchedule = "tests/tvShowSchedule.json"
		self.testTransmission =  os.path.isfile(self.configFileTransmission)

		self.tmpdir1 = unicode(tempfile.mkdtemp())
		self.tmpdir2 = unicode(tempfile.mkdtemp())
		self.transfererData = {
			"source": {"path": self.tmpdir1, "protocol": "file"},
			"destination": {"path": self.tmpdir2, "protocol": "file"},
			"delete_after":False,
			"pathPattern":"{seriesname}/season {seasonnumber}"
		}

		self.ts = torrentSearch.torrentSearch(id="torrentSearch",dataFile="tests/torrentSearch2.json",verbosity=DEBUG_TORRENT_SEARCH)
		self.t = myTvDB.myTvDB(debug=DEBUG,cache=False)

	def tearDown(self):
		shutil.rmtree(self.tmpdir1)
		shutil.rmtree(self.tmpdir2)

	def test_creation(self):
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),info={'seriesname':'Lost'},autoComplete=False)
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow['status'],0)

	@httpretty.activate
	def test_creation_without_overview_and_banner(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=111,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),info={'seriesname':'About Face'})
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow['info']['overview'],"")

	@httpretty.activate
	def test_creation_with_new_banner_dl(self):
		os.path.getmtime = mock.MagicMock(return_value=time.mktime((datetime.datetime.now() - datetime.timedelta(days=45)).timetuple()))
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		tmpdir = unicode(tempfile.mkdtemp())
		tmpfile = '{0}/banner_123.jpg'.format(tmpdir)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,bannerDir=tmpdir,autoComplete=True,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),info={'seriesname':'Lost'})
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertTrue(tvShow['info']['banner'])
		self.assertTrue(os.path.isfile(tmpfile))
		self.assertEqual(LogTestCase.md5(tmpfile),LogTestCase.md5('tests/image.jpg'))
		self.assertTrue(httpretty.has_request())
		os.remove(tmpfile)
		shutil.rmtree(tmpdir)

	@httpretty.activate
	def test_creation_with_fresh_banner(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		tmpdir = unicode(tempfile.mkdtemp())
		tmpfile = '{0}/banner_123.jpg'.format(tmpdir)
		shutil.copyfile('tests/image1.jpg',tmpfile)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,bannerDir=tmpdir,autoComplete=True,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),info={'seriesname':'Lost'})
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertTrue(tvShow['info']['banner'])
		self.assertTrue(os.path.isfile(tmpfile))
		self.assertEqual(LogTestCase.md5(tmpfile),LogTestCase.md5('tests/image1.jpg'))
		self.assertFalse(httpretty.has_request())
		os.remove(tmpfile)
		shutil.rmtree(tmpdir)

	@httpretty.activate
	def test_creation_with_outdated_banner(self):
		os.path.getmtime = mock.MagicMock(return_value=time.mktime((datetime.datetime.now() - datetime.timedelta(days=45)).timetuple()))
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		tmpdir = unicode(tempfile.mkdtemp())
		tmpfile = '{0}/banner_123.jpg'.format(tmpdir)
		shutil.copyfile('tests/image1.jpg',tmpfile)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,bannerDir=tmpdir,autoComplete=True,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),info={'seriesname':'Lost'})
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertTrue(tvShow['info']['banner'])
		self.assertTrue(os.path.isfile(tmpfile))
		self.assertEqual(LogTestCase.md5(tmpfile),LogTestCase.md5('tests/image.jpg'))
		self.assertTrue(httpretty.has_request())
		os.remove(tmpfile)
		shutil.rmtree(tmpdir)

	@httpretty.activate
	def test_delete_banner(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		tmpdir = unicode(tempfile.mkdtemp())
		tmpfile = '{0}/banner_123.jpg'.format(tmpdir)
		shutil.copyfile('tests/image1.jpg',tmpfile)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,bannerDir=tmpdir,autoComplete=True,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),info={'seriesname':'Lost'})
		tvShow.deleteBanner()
		self.assertFalse(tvShow['info']['banner'])
		self.assertFalse(os.path.isfile(tmpfile))
		shutil.rmtree(tmpdir)

	@httpretty.activate
	def test_creation_from_MyTvDB(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		t = myTvDB.myTvDB()
		tvShow = tvShowSchedule.tvShowScheduleFromMyTvDB(t[123],verbosity=DEBUG_TVSHOWSCHEDULE)
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow['status'],0)

	@httpretty.activate
	def test_creation_from_id(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowScheduleFromId(123,verbosity=DEBUG_TVSHOWSCHEDULE)
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow['status'],0)

	@httpretty.activate
	def test_get_progression(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                            ])
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)

		self.downloader.loadConfig(self.configFileTransmission)
		self.transferer.addData(self.configFileTvShowSchedule)
		self.transferer.setValue(self.transfererData)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=30,
			downloader_id = 3
		)
		self.assertEqual(tvShow.get_progression(downloader=self.downloader),75)

	@httpretty.activate
	def test_update_0_to_10(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=2,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=0
		)
		self.assertEqual(tvShow['status'],0)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],10)

	@httpretty.activate
	def test_update_0_to_22(self): # Added to waiting for torrent availability
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])

		self.downloader.loadConfig(self.configFileTransmission)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 1'},
			status=0
		)
		self.assertEqual(tvShow['status'],0)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],22)

	@httpretty.activate
	def test_update_0_to_30(self): # Added to Download in progress
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                            ])
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())

		self.downloader.loadConfig(self.configFileTransmission)

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 1'},
			status=0
		)
		self.assertEqual(tvShow['status'],0)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],30)

	@httpretty.activate
	def test_update_0_to_90(self): # Added to TvShow Achieved
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=123,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			info={'seriesname':'TvShow 1'}
		)
		self.assertEqual(tvShow['status'],0)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],90)

	@httpretty.activate
	def test_update_10_to_21(self): # not broadcasted to waiting for torrent push
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())


		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		emptyTS = torrentSearch.torrentSearch(
			id="torrentSearch",
			dataFile=tmpfile,
			verbosity=DEBUG_TORRENT_SEARCH
		)

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=10
		)
		self.assertEqual(tvShow['status'],10)

		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=emptyTS,force=True)
		self.assertEqual(tvShow['status'],21)
		os.remove(tmpfile)

	@httpretty.activate
	def test_update_10_to_22(self): # not broadcasted to waiting for torrent availability
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_not_found.json','r').read())

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=10
		)
		self.assertEqual(tvShow['status'],10)

		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],22)

	@httpretty.activate
	def test_update_10_to_30(self): # not broadcasted to Download in progress
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                            ])

		self.downloader.loadConfig(self.configFileTransmission)

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=10
		)
		self.assertEqual(tvShow['status'],10)

		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],30)

	@httpretty.activate
	def test_update_20_to_22_file_corrupt(self): # Waiting for torrent availability to itself caused by corrupted file
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent_corrupt.json','r').read()),
                            ])
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		self.downloader.loadConfig(self.configFileTransmission)

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=20
		)
		with self.assertLogs(level='ERROR'):
			tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],22)

	@httpretty.activate
	def test_update_20_to_22_downloader_connection_error(self): # Waiting for torrent availability to itself caused by connection error
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",status=500)

		self.downloader.loadConfig(self.configFileTransmission)

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=20
		)
		with self.assertLogs(level='ERROR'):
			tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],22)

	@httpretty.activate
	def test_update_20_to_30(self): # Waiting for torrent availability to Download in progress
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                            ])
		self.downloader.loadConfig(self.configFileTransmission)

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=20
		)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],30)

	@httpretty.activate
	def test_update_21_to_22(self): # pushing torrent required -to- wathing torrent on torrent providers
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_not_found.json','r').read())

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=21
		)
		self.assertEqual(tvShow['status'],21)

		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],22)

	@httpretty.activate
	def test_update_22_to_21(self): # Watching torrent from TP but no TP setup
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())


		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		emptyTS = torrentSearch.torrentSearch(
			id="torrentSearch",
			dataFile=tmpfile,
			verbosity=DEBUG_TORRENT_SEARCH
		)

		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=22
		)
		self.assertEqual(tvShow['status'],22)

		with self.assertLogs(level='ERROR'):
			tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=emptyTS,force=True)
		self.assertEqual(tvShow['status'],21)
		os.remove(tmpfile)

	@httpretty.activate
	def test_update_30_to_10(self): # Download in progress to Added
		files = ['file1.txt','file2.tgz','foo/file4.txt']

		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", body=open('tests/httpretty_kat_search_home.json','r').read())
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                            ])

		os.makedirs(self.tmpdir1+"/foo")
		for myFile in files:
			with open(self.tmpdir1+"/"+myFile, 'a'):
				os.utime(self.tmpdir1+"/"+myFile, None)
		self.downloader.loadConfig(self.configFileTransmission)
		self.transferer.addData(self.configFileTvShowSchedule)
		self.transferer.setValue(self.transfererData)
		self.transferer.data['pathPattern'] = "{seriesname}/season {seasonnumber}/episode {episodenumber}"
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=30,
			downloader_id=3
		)
		for myFile in files:
			self.assertTrue(os.path.isfile(self.tmpdir1+"/"+myFile))
			self.assertFalse(os.path.isfile(self.tmpdir2+"/"+myFile))
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		for myFile in files:
			self.assertTrue(os.path.isfile(self.tmpdir1+"/"+myFile))
			os.remove(self.tmpdir1+"/"+myFile)
			self.assertTrue(os.path.isfile(self.tmpdir2+"/TvShow 2/season 1/episode 1/"+myFile))
		self.assertEqual(tvShow['status'],10)

	@httpretty.activate
	def test_update_30_to_10_with_delete_after(self): # Download in progress to Added
		files = ['file1.txt','file2.tgz','foo/file4.txt']

		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
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
		transfererData = dict(self.transfererData)
		transfererData['delete_after'] = True
		self.transferer.setValue(transfererData)
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=1,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=30,
			downloader_id=3
		)
		for myFile in files:
			self.assertTrue(os.path.isfile(self.tmpdir1+"/"+myFile))
			self.assertFalse(os.path.isfile(self.tmpdir2+"/"+myFile))
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		for myFile in files:
			self.assertTrue(os.path.isfile(self.tmpdir1+"/"+myFile))
			os.remove(self.tmpdir1+"/"+myFile)
			self.assertTrue(os.path.isfile(self.tmpdir2+"/TvShow 2/season 1/"+myFile))
		self.assertEqual(tvShow['status'],10)

	@httpretty.activate
	def test_update_30_to_90(self): # Download in progress to Achieved
		files = ['file1.txt','file2.tgz','foo/file4.txt']

		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, T411_URL + "/torrents/search/TvShow%201%20S01E02%20720p", body=open('tests/httpretty_kat_search_not_found.json','r').read())
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
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			season=1,
			episode=2,
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=30,
			downloader_id=3
		)
		for myFile in files:
			self.assertTrue(os.path.isfile(self.tmpdir1+"/"+myFile))
			self.assertFalse(os.path.isfile(self.tmpdir2+"/"+myFile))
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		for myFile in files:
			self.assertTrue(os.path.isfile(self.tmpdir1+"/"+myFile))
			os.remove(self.tmpdir1+"/"+myFile)
			self.assertTrue(os.path.isfile(self.tmpdir2+"/TvShow 2/season 1/"+myFile))
		self.assertEqual(tvShow['status'],90)

	@httpretty.activate
	def test_update_90_to_10(self): # Achieved to watching
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=321,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 2'},
			status=90
		)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],10)

	@httpretty.activate
	def test_update_90_to_90(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
			httpretty.register_uri(httpretty.POST, mock_url[0],body=open(mock_url[1],'r').read())
		tvShow = tvShowSchedule.tvShowSchedule(seriesid=456,autoComplete=False,verbosity=DEBUG_TVSHOWSCHEDULE)
		tvShow.set(
			nextUpdate=datetime.datetime.now(),
			info={'seriesname':'TvShow 1'},
			status=90
		)
		tvShow.update(downloader=self.downloader,transferer=self.transferer,searcher=self.ts,force=True)
		self.assertEqual(tvShow['status'],90)
