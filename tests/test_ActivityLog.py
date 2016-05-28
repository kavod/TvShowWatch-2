#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import shutil
import logging
import LogTestCase
import ActivityLog

DEBUG=False

class TestActivityLog(LogTestCase.LogTestCase):
	def setUp(self):
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
		db.add_entry(
			seriesid = 123,
			oldStatus = 10,
			newStatus = 20
		)
		os.remove(tmpfile)
