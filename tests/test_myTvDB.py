#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import myTvDB

class TestMyTvDB(unittest.TestCase):
	def setUp(self):
		self.t = myTvDB.myTvDB()
		
	def test_creation(self):
		self.assertIsInstance(self.t,myTvDB.myTvDB)
		
	def test_search(self):
		self.assertIsInstance(self.t['Lost'],myTvDB.myShow)
		self.assertIsInstance(self.t['Lost'][1][1],myTvDB.myEpisode)
		
	def test_lastAired(self):
		self.lastAired = self.t['Lost'].lastAired()
		self.assertIsInstance(self.lastAired,myTvDB.myEpisode)
		self.assertEqual(self.lastAired['firstaired'],'2010-05-23')
		
	def test_nextAired_ok(self):
		self.nextAired = self.t['Plus belle la vie'].lastAired()
		self.assertIsInstance(self.nextAired,myTvDB.myEpisode)
		
	def test_nextAired_ko(self):
		self.nextAired = self.t['Lost'].nextAired()
		self.assertIsNone(self.nextAired)
		
	def test_next(self):
		self.assertIsNone(self.t['Lost'][6][18].next())
		self.assertIsInstance(self.t['Lost'][1][1].next(),myTvDB.myEpisode)
