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

DEBUG=False

class TestActivityLog(LogTestCase.LogTestCase):
	def setUp(self):
		self.dataTest = [
			{ "seriesid" : 123,
			"oldStatus" : 10,
			"newStatus" : 20
			},
			{ "seriesid" : 345,
			"oldStatus" : 10,
			"newStatus" : 30,
			"myDateTime" : time.mktime(datetime.datetime.now().timetuple())
			},
		]
		pass

	def test_creation(self):
		tmpfile = unicode(tempfile.mkstemp('.db')[1])
		os.remove(tmpfile)
		db = ActivityLog.ActivityLog(tmpfile)
		self.assertTrue(os.path.isfile(tmpfile))
		os.remove(tmpfile)

	def test_add_entry(self):
		tmpfile = unicode(tempfile.mkstemp('.db')[1])
		os.remove(tmpfile)
		db = ActivityLog.ActivityLog(tmpfile)
		db.add_entries(self.dataTest)
		os.remove(tmpfile)

	def test_add_entry(self):
		tmpfile = unicode(tempfile.mkstemp('.db')[1])
		os.remove(tmpfile)
		db = ActivityLog.ActivityLog(tmpfile)
		db.add_entry(
			seriesid = 123,
			oldStatus = 10,
			newStatus = 20
		)
		os.remove(tmpfile)

	def test_get_entry(self):
		tmpfile = unicode(tempfile.mkstemp('.db')[1])
		os.remove(tmpfile)
		db = ActivityLog.ActivityLog(tmpfile)
		db.add_entries(self.dataTest)
		self.assertEquals(len(db.get_entry(oldStatus = 10)),2)
		os.remove(tmpfile)
