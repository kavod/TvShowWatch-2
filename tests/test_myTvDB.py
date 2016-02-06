#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import myTvDB
import httpretty
import requests

httpretty_urls = [
	("http://thetvdb.com/api/GetSeries.php",'tests/httpretty_myTvDB1'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/en.xml",'tests/httpretty_myTvDB2'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/all/en.xml",'tests/httpretty_myTvDB3'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/en.xml",'tests/httpretty_myTvDB4'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/all/en.xml",'tests/httpretty_myTvDB5')
				]

class TestMyTvDB(unittest.TestCase):
	def setUp(self):
		self.t = myTvDB.myTvDB(debug=False,cache=False)
		
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
	def test_next(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.assertIsNone(self.t['TvShow1'][1][2].next())
		self.assertIsInstance(self.t['TvShow1'][1][1].next(),myTvDB.myEpisode)
