#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import json
import datetime
import dateutil.parser
import tempfile
import shutil
import httpretty
import logging
import myTvDB
import torrentProvider
import Downloader
import Transferer
import torrentSearch
import tvShowSchedule
import tvShowList

httpretty.HTTPretty.allow_net_connect = False

T411_URL = (item for item in torrentProvider.TRACKER_CONF if item["id"] == "t411").next()['url']

httpretty_urls = [
	("http://thetvdb.com/api/GetSeries.php",'tests/httpretty_myTvDB1.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/en.xml",'tests/httpretty_myTvDB2.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/all/en.xml",'tests/httpretty_myTvDB3.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/en.xml",'tests/httpretty_myTvDB4.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/all/en.xml",'tests/httpretty_myTvDB5.xml'),
	("http://thetvdb.com/banners/_cache/graphical/123-g4.jpg",'tests/image.jpg'),
	("http://thetvdb.com/banners/_cache/graphical/321-g4.jpg",'tests/image.jpg'),
	(T411_URL + "/auth",'tests/httpretty_t411_auth.json'),
	(T411_URL + "/users/profile/12345678",'tests/httpretty_t411_auth.json'),
	(T411_URL + "/torrents/search/home",'tests/httpretty_t411_search_home.json'),
	(T411_URL + "/torrents/search/TvShow%201%20S01E01%20720p",'tests/httpretty_t411_search_not_found.json'),
	(T411_URL + "/torrents/download/4711811",'tests/httpretty_t411_download.torrent'),
	("https://torcache.net/torrent/F261769DEEF448D86B23A8A0F2CFDEF0F64113C9.torrent",'tests/httpretty_kat_download_home.magnet'),
				]
DEBUG=False

class TestTvShowList(unittest.TestCase):
	@httpretty.activate
	def setUp(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.t = myTvDB.myTvDB(debug=DEBUG,cache=False)
		self.id1 = 123
		self.id2 = 321
		self.title1 = 'TvShow 1'
		self.title2 = 'TvShow 2'
		self.tvShow1 = self.t[self.id1]
		self.tvShow2 = self.t[self.id2]
		self.d1 = [{"seriesid":self.id1,"title":self.title1,"status":0}]
		self.tvShowSchedule1 = tvShowSchedule.tvShowSchedule(seriesid=self.id1, verbosity=DEBUG)
		self.tvShowSchedule2 = tvShowSchedule.tvShowSchedule(seriesid=self.id2, verbosity=DEBUG)
		self.tmpdir1 = unicode(tempfile.mkdtemp())
		self.tmpdir2 = unicode(tempfile.mkdtemp())
		self.tmpdirBanner = unicode(tempfile.mkdtemp())

	def tearDown(self):
		shutil.rmtree(self.tmpdir1)
		shutil.rmtree(self.tmpdir2)
		shutil.rmtree(self.tmpdirBanner)

	def loadFullConfig(self):
		self.confFilename = "tests/fullConfig.json"
		self.downloader = Downloader.Downloader(verbosity=DEBUG)
		self.downloader.loadConfig(self.confFilename)
		self.transferer = Transferer.Transferer(id="transferer",verbosity=DEBUG)
		self.transfererData = {"source": {"path": self.tmpdir1, "protocol": "file"}, "destination": {"path": self.tmpdir2, "protocol": "file"}}
		self.transferer.addData(self.confFilename)
		self.transferer.setValue(self.transfererData)
		self.torrentSearch = torrentSearch.torrentSearch(id="torrentSearch",dataFile=self.confFilename,verbosity=DEBUG)

	def creation(self):
		self.l1 = tvShowList.tvShowList(banner_dir=self.tmpdirBanner,verbosity=DEBUG)

	def test_creation(self):
		self.creation()
		self.assertIsInstance(self.l1,tvShowList.tvShowList)
		self.assertEqual(self.l1,[])

	def test_loadFile(self):
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		shutil.copyfile('tests/tvShowList1.json',tmpfile)

		self.creation()
		self.l1.addData(tmpfile)
		self.assertEqual(len(self.l1),3)

		os.remove(tmpfile)

	@httpretty.activate
	def test_save(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShow1)
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		self.l1.save(filename=tmpfile)
		with open(tmpfile) as data_file:
			data = json.load(data_file)
		self.assertTrue('nextUpdate' in data['tvShowList'][0].keys())
		self.assertTrue(isinstance(dateutil.parser.parse(data['tvShowList'][0]['nextUpdate']),datetime.datetime))
		del(data['tvShowList'][0]['nextUpdate'])
		del(data['tvShowList'][0]['info']['infoUpdate'])
		self.maxDiff=None
		self.assertEqual({
			'tvShowList':[
				{
					'seriesid':self.id1,
					'status':0,
					'season':0,
					'episode':0,
					'downloader_id':'',
					'pattern':self.title1.lower(),
					'info':{
						'banner':True,
						'overview': 'This is the description of the TvShow number 1 used by myTvDB class tests.',
						'seriesname':self.title1,
						'episodesList': [0, 2]
					},
					'emails':[],
					'keywords': []
				}
			]
		},data),
		os.remove(tmpfile)

	@httpretty.activate
	def test_add_TvShow_achieved(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShow1)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],0)
		self.assertEqual(self.l1[0]['episode'],0)

	@httpretty.activate
	def test_add_TvShow_from_id(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.id1)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],0)
		self.assertEqual(self.l1[0]['episode'],0)

	@httpretty.activate
	def test_add_TvShow_from_tvShowSchedule(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.tvShowSchedule1
		self.l1.add(self.tvShowSchedule1)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],0)
		self.assertEqual(self.l1[0]['episode'],0)
		self.assertEqual(self.l1[0]['status'],0)

	@httpretty.activate
	def test_add_TvShow_with_episode(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.id1,season=1,epno=2)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],1)
		self.assertEqual(self.l1[0]['episode'],2)

	@httpretty.activate
	def test_add_TvShow_with_wrong_episode(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		with self.assertRaises(Exception):
			self.l1.add(tvShow=self.id1,season=7,epno=2)
		self.assertEqual(len(self.l1),0)

	@httpretty.activate
	def test_add_TvShow_already_in(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.id1)
		with self.assertRaises(Exception):
			self.l1.add(self.tvShow1)
		self.assertEqual(len(self.l1),1)

	@httpretty.activate
	def test_add_TvShow_multi(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.id1)
		self.l1.add(self.tvShow2)
		self.assertEqual(len(self.l1),2)

	@httpretty.activate
	def test_inList(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShow1)
		self.assertTrue(self.l1.inList(self.id1))
		self.assertTrue(self.l1.inList(self.tvShow1))
		self.assertFalse(self.l1.inList(self.tvShow2))

	@httpretty.activate
	def test_getTvShow(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShow1)
		self.assertEqual(self.l1.getTvShow(self.id1)['seriesid'],self.id1)
		self.assertIsNone(self.l1.getTvShow(self.id2))

	@httpretty.activate
	def test_delete(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShow1)
		self.l1.add(self.tvShow2)
		self.assertTrue(self.l1.inList(self.id1))
		self.assertTrue(self.l1.inList(self.id2))
		self.assertTrue(os.path.isfile('{0}/banner_{1}.jpg'.format(self.tmpdirBanner,self.id1)))
		self.assertTrue(os.path.isfile('{0}/banner_{1}.jpg'.format(self.tmpdirBanner,self.id2)))
		self.l1.delete(self.id2)
		self.assertTrue(os.path.isfile('{0}/banner_{1}.jpg'.format(self.tmpdirBanner,self.id1)))
		self.assertFalse(os.path.isfile('{0}/banner_{1}.jpg'.format(self.tmpdirBanner,self.id2)))
		self.assertTrue(self.l1.inList(self.id1))
		self.assertFalse(self.l1.inList(self.id2))
		self.l1.add(self.tvShow2)
		self.l1.delete(self.id1)
		self.assertFalse(self.l1.inList(self.id1))
		self.assertTrue(self.l1.inList(self.id2))
		self.assertRaises(Exception,self.l1.delete,999)

	@httpretty.activate
	def test_update(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		httpretty.register_uri(httpretty.POST, "https://kat.cr/json.php", responses=[
							   httpretty.Response(body=open('tests/httpretty_kat_search_not_found.json','r').read()),
							   httpretty.Response(body=open('tests/httpretty_kat_search_not_found.json','r').read()),
							   httpretty.Response(body=open('tests/httpretty_kat_search_not_found.json','r').read()),
							   httpretty.Response(body=open('tests/httpretty_kat_search_not_found.json','r').read()),
							   httpretty.Response(body=open('tests/httpretty_kat_search_home.json','r').read()),
							   httpretty.Response(body=open('tests/httpretty_kat_search_home.json','r').read())
							   ])
		httpretty.register_uri(httpretty.POST, "http://localhost:9091/transmission/rpc",responses=[
                               httpretty.Response(body=open('tests/httpretty_transmission_get_session.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_add_torrent.json','r').read()),
                               httpretty.Response(body=open('tests/httpretty_transmission_torrent_get_downloading.json','r').read()),
                              ])

		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		shutil.copyfile('tests/tvShowList3.json',tmpfile)

		self.loadFullConfig()
		myList = tvShowList.tvShowList(banner_dir=self.tmpdirBanner,tvShows=tmpfile,verbosity=DEBUG)

		self.assertEqual(myList[0]['status'],0) # 321 S1E2 0 => 10
		self.assertEqual(myList[1]['status'],0) # 123 S1E1 0 => 20
		myList.update(downloader=self.downloader,transferer=self.transferer,searcher=self.torrentSearch,wait=True,force=True)
		self.assertEqual(myList[0]['status'],10) # 321 S1E2 0 => 10
		self.assertEqual(myList[1]['status'],20) # 123 S1E1 0 => 20

		myList[0].set(season=1,episode=1,status=10)
		myList[1].set(status=0)
		self.assertEqual(myList[0]['status'],10) # 321 S1E1 10 => 20
		self.assertEqual(myList[1]['status'],0) # 123 S1E1 0 => 30
		myList.update(wait=True,force=True)
		self.assertEqual(myList[0]['status'],20) # 321 S1E1 10 => 20
		self.assertEqual(myList[1]['status'],30) # 123 S1E1 0 => 30

		#myList[0].set(season=1,episode=1,status=10)
		myList[1].set(season=1,episode=1,status=10)
		self.assertEqual(myList[0]['status'],20) # 321 S1E1 20 => 30
		self.assertEqual(myList[1]['status'],10) # 123 S1E1 10 => 30
		myList.update(wait=True,force=True)
		self.assertEqual(myList[0]['status'],30) # 321 S1E1 20 => 30
		self.assertEqual(myList[1]['status'],30) # 123 S1E1 10 => 30

		os.remove(tmpfile)

	@httpretty.activate
	def test_getValue(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShow1)
		self.l1.add(self.tvShow2)
		self.assertEquals(self.l1.getValue()[0]['seriesid'],123)
		self.assertEquals(self.l1.getValue()[1]['seriesid'],321)
