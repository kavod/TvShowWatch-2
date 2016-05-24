#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import myTvDB
import httpretty
import requests

httpretty_urls = [
	("http://thetvdb.com/api/GetSeries.php",'tests/httpretty_myTvDB1.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/en.xml",'tests/httpretty_myTvDB2.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/all/en.xml",'tests/httpretty_myTvDB3.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/en.xml",'tests/httpretty_myTvDB4.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/all/en.xml",'tests/httpretty_myTvDB5.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/456/en.xml",'tests/httpretty_myTvDB4.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/456/all/en.xml",'tests/httpretty_myTvDB7.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/222/en.xml",'tests/httpretty_myTvDB_next_episode_wo_firstaired_showInfo.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/222/all/en.xml",'tests/httpretty_myTvDB_next_episode_wo_firstaired_episodesInfo.xml')
				]
DEBUG=True

class TestMyTvDB(unittest.TestCase):
	def setUp(self):
		self.t = myTvDB.myTvDB(debug=DEBUG,cache=False)

	def test_creation(self):
		self.assertIsInstance(self.t,myTvDB.myTvDB)

	@httpretty.activate
	def test_search(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.assertIsInstance(self.t['TvShow1'],myTvDB.myShow)
		self.assertIsInstance(self.t['TvShow1'][1][1],myTvDB.myEpisode)

	@httpretty.activate
	def test_lastAired(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.lastAired = self.t['TvShow1'].lastAired()
		self.assertIsInstance(self.lastAired,myTvDB.myEpisode)
		self.assertEqual(self.lastAired['firstaired'],'2010-05-23')

	@httpretty.activate
	def test_nextAired_ok(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.nextAired = self.t[321].lastAired()
		self.assertIsInstance(self.nextAired,myTvDB.myEpisode)

	@httpretty.activate
	def test_nextAired_ko(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.nextAired = self.t['TvShow1'].nextAired()
		self.assertIsNone(self.nextAired)

	@httpretty.activate
	def test_nextAired_with_empty_season(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.nextAired = self.t[456].nextAired()
		self.assertIsNone(self.nextAired)

	@httpretty.activate
	def test_next(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.assertIsNone(self.t['TvShow1'][1][2].next())
		self.assertIsInstance(self.t['TvShow1'][1][1].next(),myTvDB.myEpisode)

	@httpretty.activate
	def test_next_wo_firstaired(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.assertIsNone(self.t[222][1][1].next())

	@httpretty.activate
	def test_getEpisodesList(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.assertEquals(self.t[123].getEpisodesList(),{1:2})
		self.assertEquals(self.t[456].getEpisodesList(),{1:2})
