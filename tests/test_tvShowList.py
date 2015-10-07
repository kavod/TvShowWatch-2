#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import json
import myTvDB
import tvShowList
import tempfile
import JSAG

class TestTvShowList(unittest.TestCase):
	def setUp(self):
		self.t = myTvDB.myTvDB()
		self.idLost = 73739
		self.idDexter = 79349
		self.titleLost = 'Lost'
		self.titleDexter = 'Dexter'
		self.tvShowLost = self.t[self.idLost]
		self.tvShowDexter = self.t[self.idDexter]
		self.d1 = [{"id":self.idLost,"title":self.titleLost,"status":0}]
		
	def test_creation(self):
		self.l1 = tvShowList.tvShowList()
		self.assertIsInstance(self.l1,tvShowList.tvShowList)
		self.assertEqual(len(self.l1),0)
		
	def test_loadFile(self):
		self.test_creation()
		self.l1.loadFile('tests/tvShowList1.json',path=[])
		self.assertEqual(len(self.l1),3)
	
	def test_save(self):
		self.test_creation()
		self.l1.add(self.tvShowLost)
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		self.l1.save(filename=tmpfile,path=['tvShowList'])
		with open(tmpfile) as data_file:    
			data = json.load(data_file)
		self.assertEqual({'tvShowList':[{'id':self.idLost,'title':self.titleLost,'status':0,'season':1,'episode':1}]},data),
		os.remove(tmpfile)
		
	def test_add_TvShow_achieved(self):
		self.test_creation()
		self.l1.add(self.tvShowLost)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(JSAG.toJSON(self.l1.tvList[0]['season']),1)
		self.assertEqual(JSAG.toJSON(self.l1.tvList[0]['episode']),1)
		
	def test_add_TvShow_from_id(self):
		self.test_creation()
		self.l1.add(self.idLost)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(JSAG.toJSON(self.l1.tvList[0]['season']),1)
		self.assertEqual(JSAG.toJSON(self.l1.tvList[0]['episode']),1)
		
	def test_add_TvShow_with_episode(self):
		self.test_creation()
		self.l1.add(self.idLost,season=2,epno=2)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(JSAG.toJSON(self.l1.tvList[0]['season']),2)
		self.assertEqual(JSAG.toJSON(self.l1.tvList[0]['episode']),2)
		
	def test_add_TvShow_with_wrong_episode(self):
		self.test_creation()
		with self.assertRaises(Exception):
			self.l1.add(self.idLost,season=7,epno=2)
		self.assertEqual(len(self.l1),0)
		
	def test_add_TvShow_already_in(self):
		self.test_creation()
		self.l1.add(self.idLost)
		with self.assertRaises(Exception):
			self.l1.add(self.tvShowLost)
		self.assertEqual(len(self.l1),1)
	
	def test_add_TvShow_multi(self):
		self.test_creation()
		self.l1.add(self.idLost)
		self.l1.add(self.tvShowDexter)
		self.assertEqual(len(self.l1),2)
		
	def test_inList(self):
		self.test_creation()
		self.l1.add(self.tvShowLost)
		self.assertTrue(self.l1.inList(self.idLost))
		self.assertTrue(self.l1.inList(self.tvShowLost))
		self.assertFalse(self.l1.inList(self.tvShowDexter))
		
