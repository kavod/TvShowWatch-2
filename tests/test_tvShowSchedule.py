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

class TestTvShowSchedule(unittest.TestCase):
	def setUp(self):
		tvShowSchedule.resetTvDB()
		
	def fakeTvDB(self):
		t = myTvDB.myTvDB()
		t[73739][6][18]['firstaired'] = '2099-12-31'
		tvShowSchedule.fakeTvDB(t)
	
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
		self.fakeTvDB()
		
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=6,episode=18,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(force=True)
		self.assertEqual(tvShow.status,10)
		
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=0,episode=0,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(force=True)
		self.assertEqual(tvShow.status,10)
		
	def test_update_0_to_20(self):
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(force=True)
		self.assertEqual(tvShow.status,20)
		
	def test_update_0_to_90(self):
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=0,episode=0,status=0,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,0)
		tvShow.update(force=True)
		self.assertEqual(tvShow.status,90)
		
	def test_update_90_to_10(self):
		self.fakeTvDB()		
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=0,episode=0,status=90,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,90)
		tvShow.update(force=True)
		self.assertEqual(tvShow.status,10)
		
	def test_update_90_to_90(self):
		tvShow = tvShowSchedule.tvShowSchedule(id=73739,title='Lost',season=0,episode=0,status=90,nextUpdate=datetime.datetime.now())
		self.assertEqual(tvShow.status,90)
		tvShow.update(force=True)
		self.assertEqual(tvShow.status,90)
