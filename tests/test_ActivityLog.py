#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import shutil
import datetime
import time
import logging
import LogTestCase
import ActivityLog

DEBUG=logging.WARNING

class TestActivityLog(LogTestCase.LogTestCase):
	def setUp(self):
		curPath = os.path.dirname(os.path.realpath(__file__))
		self.filename1 = curPath + "/activityLog1.db"
		self.dataTest = [
			{ "seriesid" : 123,
			"season":2,
			"episode":7,
			"oldStatus" : 10,
			"newStatus" : 20,
			"type":"info"
			},
			{ "seriesid" : 345,
			"season":2,
			"episode":7,
			"oldStatus" : 10,
			"newStatus" : 30,
			"type":"info",
			"datetime" : int(time.mktime(datetime.datetime.now().timetuple()))
			},
		]
		pass

	def test_creation(self):
		tmpfile = unicode(tempfile.mkstemp('.db')[1])
		os.remove(tmpfile)
		db = ActivityLog.ActivityLog(tmpfile,verbosity=DEBUG)
		self.assertTrue(os.path.isfile(tmpfile))
		os.remove(tmpfile)

	def test_addEntry(self):
		tmpfile = unicode(tempfile.mkstemp('.db')[1])
		os.remove(tmpfile)
		db = ActivityLog.ActivityLog(tmpfile,verbosity=DEBUG)
		db.add_entries(self.dataTest)
		data = db.get_entry(seriesid = 345)
		self.assertEquals(len(data),1)
		for key in self.dataTest[1].keys():
			self.assertEquals(data[0][key],self.dataTest[1][key])
		data = db.get_entry(seriesid = 123)
		self.assertEquals(len(data),1)
		for key in self.dataTest[0].keys():
			self.assertEquals(data[0][key],self.dataTest[0][key])
		os.remove(tmpfile)

	def test_add_entry(self):
		tmpfile = unicode(tempfile.mkstemp('.db')[1])
		os.remove(tmpfile)
		db = ActivityLog.ActivityLog(tmpfile,verbosity=DEBUG)
		db.add_entry(
			seriesid = 123,
			season = 2,
			episode = 7,
			oldStatus = 10,
			newStatus = 20,
			type = "info"
		)
		os.remove(tmpfile)

	def test_get_entry(self):
		tmpfile = unicode(tempfile.mkstemp('.db')[1])
		os.remove(tmpfile)
		shutil.copyfile(self.filename1,tmpfile)
		db = ActivityLog.ActivityLog(tmpfile,verbosity=DEBUG)
		self.assertEquals(len(db.get_entry(seriesid = 123)),4)
		os.remove(tmpfile)
