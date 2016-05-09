#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import datetime
import time
import shutil
import unittest
import mock
import httpretty
import logging
import tempfile
import LogTestCase
import ScriptCache
httpretty.HTTPretty.allow_net_connect = False
DEBUG = logging.WARNING

class TestScriptCache(LogTestCase.LogTestCase):
	def setUp(self):
		logger = logging.getLogger("ScriptCache.google.html")
		logger.setLevel(DEBUG)
		self.tmpdir = unicode(tempfile.mkdtemp())
		self.localFile = "google.html"
		self.remoteURL = "http://www.google.com/"
		self.body = "This is the Google homepage"
		self.localFileAbsPath = "{0}/{1}".format(self.tmpdir,self.localFile)
	
	def tearDown(self):
		shutil.rmtree(self.tmpdir)
	
	@httpretty.activate
	def test_initialization(self):
		if os.path.isfile(self.localFileAbsPath):
			os.remove(self.localFileAbsPath)
		httpretty.register_uri(httpretty.GET, self.remoteURL, body=self.body)
		sc = ScriptCache.ScriptCache(remoteURL=self.remoteURL,localFile=self.localFile,directory=self.tmpdir)
		self.assertIsInstance(sc,ScriptCache.ScriptCache)
		self.assertTrue(httpretty.has_request())
		self.assertTrue(os.path.isfile(self.localFileAbsPath))
		with open(self.localFileAbsPath) as fd:
			self.assertEquals(fd.read(),self.body)
	
	@httpretty.activate
	def test_existingFile(self):
		httpretty.register_uri(httpretty.GET, self.remoteURL, body=self.body)
		with open(self.localFileAbsPath,'w') as fd:
			fd.write(self.body)
		time.sleep(1)
		lastModif = os.path.getmtime(self.localFileAbsPath)
		sc = ScriptCache.ScriptCache(remoteURL=self.remoteURL,localFile=self.localFile,directory=self.tmpdir)
		self.assertIsInstance(sc,ScriptCache.ScriptCache)
		self.assertFalse(httpretty.has_request())
		self.assertTrue(os.path.isfile(self.localFileAbsPath))
		with open(self.localFileAbsPath) as fd:
			self.assertEquals(fd.read(),self.body)
		self.assertEquals(lastModif,os.path.getmtime(self.localFileAbsPath))
		
	@httpretty.activate
	def test_outdatedFile(self):
		httpretty.register_uri(httpretty.GET, self.remoteURL, body=self.body)
		v45DaysAgo = time.mktime((datetime.datetime.now() - datetime.timedelta(days=45)).timetuple())
		getmtimeBackup = os.path.getmtime
		open(self.localFileAbsPath,'w').close()
		time.sleep(1)
		lastModif = os.path.getmtime(self.localFileAbsPath)
		os.path.getmtime = mock.MagicMock(return_value=v45DaysAgo)
		sc = ScriptCache.ScriptCache(remoteURL=self.remoteURL,localFile=self.localFile,directory=self.tmpdir)
		os.path.getmtime = getmtimeBackup
		self.assertIsInstance(sc,ScriptCache.ScriptCache)
		self.assertTrue(httpretty.has_request())
		self.assertTrue(os.path.isfile(self.localFileAbsPath))
		with open(self.localFileAbsPath) as fd:
			self.assertEquals(fd.read(),self.body)
		
