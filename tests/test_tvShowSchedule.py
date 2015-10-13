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
		pass
	
	def test_creation(self):
		tvShow = tvShowSchedule.tvShowSchedule(id=121361,title='Lost',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now())
		self.assertIsInstance(tvShow,tvShowSchedule.tvShowSchedule)
		
	def test_creation_from_MyTvDB(self):
		t = myTvDB.myTvDB()
		self.assertIsInstance(tvShowSchedule.tvShowScheduleFromMyTvDB(t['Lost']),tvShowSchedule.tvShowSchedule)
		
	def test_creation_from_id(self):
		self.assertIsInstance(tvShowSchedule.tvShowScheduleFromId(121361),tvShowSchedule.tvShowSchedule)
