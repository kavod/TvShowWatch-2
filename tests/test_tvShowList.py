#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import json
import myTvDB
import tvShowList
import tempfile

class TestTvShowList(unittest.TestCase):
	def setUp(self):
		self.t = myTvDB.myTvDB()
		self.idLost = 73739
		self.titleLost = 'Lost'
		self.tvShowLost = self.t[self.idLost]
		self.d1 = [{"id":self.idLost,"title":self.titleLost,"status":0}]
		
	def test_creation(self):
		self.l1 = tvShowList.tvShowList()
		self.assertIsInstance(self.l1,tvShowList.tvShowList)
		self.assertEqual(len(self.l1),0)
		
	def test_loadFile(self):
		self.test_creation()
		self.l1.loadFile('tests/tvShowList1.json',path=[])
		self.assertEqual(len(self.l1),3)
