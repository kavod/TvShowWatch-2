#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import datetime
import json
import myTvDB
import tvShowSchedule
import tempfile
import JSAG
import Downloader
import torrentSearch

class TestTvShowSchedule(unittest.TestCase):
	def setUp(self):
		tvShowSchedule.resetTvDB()
		self.downloader = Downloader.Downloader()
		self.configFileTransmission = "tests/downloaderTransmission.json"
		self.testTransmission =  os.path.isfile(self.configFileTransmission)
		
		t411LoginFile = os.path.dirname(os.path.abspath(__file__)) + '/loginT411.json'
		self.ts = torrentSearch.torrentSearch()
		self.ts.loadConfig("tests/torrentSearch1.json")
		if os.path.isfile(t411LoginFile):
			with open(t411LoginFile) as data_file:    
				data = json.load(data_file)
			self.ts.conf['providers'].insert(0,{'id':'t411','config':data})
		self.t = myTvDB.myTvDB()
		
	def fakeTvDB(self,id,season,episode,date):
		self.t[id][season][episode]['firstaired'] = date
		tvShowSchedule.fakeTvDB(self.t)
	
	def test_creation(self):
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now())
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow.status,0)
		
	def test_creation_from_MyTvDB(self):
		t = myTvDB.myTvDB()
		tvShow = tvShowSchedule.tvShowScheduleFromMyTvDB(t['Lost'])
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow.status,90)
		
	def test_creation_from_id(self):
		tvShow = tvShowSchedule.tvShowScheduleFromId(121361)
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		self.assertEqual(tvShow.status,90)
		
	def test_update_0_to_10(self):
		self.fakeTvDB(73739,6,18,'2099-12-31')
		
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=6,episode=18,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,10)
		
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=0,episode=0,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,10)
		
	def test_update_0_to_20(self):
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		self.downloader.loadConfig(self.configFileTransmission)
		
		tvShow = tvShowSchedule.tvShowSchedule(id=79158,title='Once Upon a Time... Life',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,20)
		
	def test_update_0_to_30(self):
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		self.downloader.loadConfig(self.configFileTransmission)
		
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,30)
		
	def test_update_0_to_90(self):
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=0,episode=0,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,90)
		
	def test_update_10_to_20(self):
		self.fakeTvDB(79158,1,26,'2099-12-31')
		
		tvShow = tvShowSchedule.tvShowSchedule(id=79158,title='Once Upon a Time... Life',season=1,episode=26,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,10)
		
		self.fakeTvDB(79158,1,26,'1987-06-17')
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,20)
		
	def test_update_10_to_30(self):
		if not self.testTransmission:
			print "No configuration for Transmission in file {0}, skipping specific tests".format(self.configFileTransmission)
		self.downloader.loadConfig(self.configFileTransmission)
		
		self.fakeTvDB(79349,8,12,'2099-12-31')
		tvShow = tvShowSchedule.tvShowSchedule(id=79349,title='Dexter',season=8,episode=12,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,10)
		
		self.fakeTvDB(79349,8,12,'2013-09-22')
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,30)
		
	def test_update_90_to_10(self):
		self.fakeTvDB(73739,6,18,'2099-12-31')	
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=0,episode=0,status=90,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,90)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,10)
		
	def test_update_90_to_90(self):
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=0,episode=0,status=90,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,90)
		tvShow.update(downloader=self.downloader,searcher=self.ts,force=True)
		self.assertEqual(tvShow.status,90)
