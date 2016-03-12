#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import json
import myTvDB
import tvShowList
import tempfile
import httpretty

httpretty_urls = [
	("http://thetvdb.com/api/GetSeries.php",'tests/httpretty_myTvDB1.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/en.xml",'tests/httpretty_myTvDB2.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/123/all/en.xml",'tests/httpretty_myTvDB3.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/en.xml",'tests/httpretty_myTvDB4.xml'),
	("http://thetvdb.com/api/A2894E6CB335E443/series/321/all/en.xml",'tests/httpretty_myTvDB5.xml')
				]
				
DEBUG=False

class TestTvShowList(unittest.TestCase):
	@httpretty.activate
	def setUp(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.t = myTvDB.myTvDB(debug=DEBUG,cache=False)
		self.idLost = 123
		self.idDexter = 321
		self.titleLost = 'TvShow 1'
		self.titleDexter = 'TvShow 2'
		self.tvShowLost = self.t[self.idLost]
		self.tvShowDexter = self.t[self.idDexter]
		self.d1 = [{"seriesid":self.idLost,"title":self.titleLost,"status":0}]
		
	def creation(self):
		self.l1 = tvShowList.tvShowList(verbosity=DEBUG)
		
	def test_creation(self):
		self.creation()
		self.assertIsInstance(self.l1,tvShowList.tvShowList)
		self.assertEqual(self.l1.getValue(),[])
		
	def test_loadFile(self):
		self.creation()
		self.l1.addData('tests/tvShowList1.json')
		self.assertEqual(len(self.l1),3)
	
	@httpretty.activate
	def test_save(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShowLost)
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		self.l1.save(filename=tmpfile)
		with open(tmpfile) as data_file:    
			data = json.load(data_file)
		self.assertEqual({'tvShowList':[{'seriesid':self.idLost,'title':self.titleLost,'status':0,'season':1,'episode':1}]},data),
		os.remove(tmpfile)
		
	@httpretty.activate
	def test_add_TvShow_achieved(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShowLost)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],1)
		self.assertEqual(self.l1[0]['episode'],1)
		
	@httpretty.activate
	def test_add_TvShow_from_id(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.idLost)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],1)
		self.assertEqual(self.l1[0]['episode'],1)
		
	@httpretty.activate
	def test_add_TvShow_with_episode(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.idLost,season=1,epno=2)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],1)
		self.assertEqual(self.l1[0]['episode'],2)
		
	@httpretty.activate
	def test_add_TvShow_with_wrong_episode(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		with self.assertRaises(Exception):
			self.l1.add(self.idLost,season=7,epno=2)
		self.assertEqual(len(self.l1),0)
		
	@httpretty.activate
	def test_add_TvShow_already_in(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.idLost)
		with self.assertRaises(Exception):
			self.l1.add(self.tvShowLost)
		self.assertEqual(len(self.l1),1)
	
	@httpretty.activate
	def test_add_TvShow_multi(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.idLost)
		self.l1.add(self.tvShowDexter)
		self.assertEqual(len(self.l1),2)
		
	@httpretty.activate
	def test_inList(self):
		for mock_url in httpretty_urls:
			httpretty.register_uri(httpretty.GET, mock_url[0],body=open(mock_url[1],'r').read())
		self.creation()
		self.l1.add(self.tvShowLost)
		self.assertTrue(self.l1.inList(self.idLost))
		self.assertTrue(self.l1.inList(self.tvShowLost))
		self.assertFalse(self.l1.inList(self.tvShowDexter))
		
