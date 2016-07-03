#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import json
import datetime
import dateutil.parser
import tempfile
import shutil
import logging
import myTvDB
import torrentProvider
import Downloader
import Transferer
import torrentSearch
import tvShowSchedule
import tvShowList
import wwwoman

T411_URL = (item for item in torrentProvider.TRACKER_CONF if item["id"] == "t411").next()['url']

DEBUG=False
DEBUG_TVSHOWLIST=DEBUG
DEBUG_DOWNLOADER=DEBUG
wwwoman.wwwomanScenario.scenario_path = "tests/wwwoman/scenario"

class TestTvShowList(unittest.TestCase):
	@wwwoman.register_scenario("thetvdb.json")
	def setUp(self):
		self.t = myTvDB.myTvDB(debug=DEBUG,cache=False)
		self.id1 = 123
		self.id2 = 321
		self.title1 = 'TvShow 1'
		self.title2 = 'TvShow 2'
		self.tvShow1 = self.t[self.id1]
		self.tvShow2 = self.t[self.id2]
		self.d1 = [{"seriesid":self.id1,"title":self.title1,"status":0}]
		self.tmpdir1 = unicode(tempfile.mkdtemp())
		self.tmpdir2 = unicode(tempfile.mkdtemp())
		self.tmpdirBanner = unicode(tempfile.mkdtemp())

	def tearDown(self):
		shutil.rmtree(self.tmpdir1)
		shutil.rmtree(self.tmpdir2)
		shutil.rmtree(self.tmpdirBanner)

	def loadFullConfig(self):
		self.confFilename = "tests/fullConfig.json"
		self.downloader = Downloader.Downloader(verbosity=DEBUG_DOWNLOADER)
		self.downloader.loadConfig(self.confFilename)
		self.transferer = Transferer.Transferer(id="transferer",verbosity=DEBUG)
		self.transfererData = {"enable":True,"source": {"path": self.tmpdir1, "protocol": "file"}, "destination": {"path": self.tmpdir2, "protocol": "file"}}
		self.transferer.addData(self.confFilename)
		self.transferer.setValue(self.transfererData)
		self.torrentSearch = torrentSearch.torrentSearch(id="torrentSearch",dataFile=self.confFilename,verbosity=DEBUG)

	def creation(self):
		self.l1 = tvShowList.tvShowList(banner_dir=self.tmpdirBanner,verbosity=DEBUG)
		self.tvShowSchedule1 = tvShowSchedule.tvShowSchedule(seriesid=self.id1, verbosity=DEBUG)

	def test_creation(self):
		self.creation()
		self.assertIsInstance(self.l1,tvShowList.tvShowList)
		self.assertEqual(self.l1,[])

	@wwwoman.register_scenario("tvShowList1.json")
	def test_loadFile(self):
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		shutil.copyfile('tests/tvShowList2.json',tmpfile)

		self.creation()
		self.l1.addData(tmpfile)
		self.assertEqual(len(self.l1),2)

		os.remove(tmpfile)

	@wwwoman.register_scenario("tvShowList1.json")
	def test_save(self):
		self.creation()
		self.l1.add(self.tvShow1)
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		self.l1.save(filename=tmpfile)
		with open(tmpfile) as data_file:
			data = json.load(data_file)
		self.assertTrue('nextUpdate' in data['tvShowList'][0].keys())
		self.assertTrue(isinstance(dateutil.parser.parse(data['tvShowList'][0]['nextUpdate']),datetime.datetime))
		del(data['tvShowList'][0]['nextUpdate'])
		del(data['tvShowList'][0]['info']['infoUpdate'])
		self.maxDiff=None
		self.assertEqual({
			'tvShowList':[
				{
					'seriesid':self.id1,
					'status':0,
					'season':0,
					'episode':0,
					'downloader_id':'',
					'pattern':self.title1.lower(),
					'info':{
						'banner':True,
						'overview': 'This is the description of the TvShow number 1 used by myTvDB class tests.',
						'seriesname':self.title1,
						'episodesList': [0, 2]
					},
					'emails':[],
					'keywords': []
				}
			]
		},data),
		os.remove(tmpfile)

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_achieved(self):
		self.creation()
		self.l1.add(self.tvShow1)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],0)
		self.assertEqual(self.l1[0]['episode'],0)

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_from_id(self):
		self.creation()
		self.l1.add(self.id1)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],0)
		self.assertEqual(self.l1[0]['episode'],0)
		self.assertEqual(self.l1[0]['keywords'],[])

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_from_id_with_defaultKeywords(self):
		self.creation()
		self.l1.add(self.id1,keywords=['niouf','niorf'])
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],0)
		self.assertEqual(self.l1[0]['episode'],0)
		self.assertEqual(self.l1[0]['keywords'],['niouf','niorf'])

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_from_tvShowSchedule(self):
		self.creation()
		self.tvShowSchedule1
		self.l1.add(self.tvShowSchedule1)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],0)
		self.assertEqual(self.l1[0]['episode'],0)
		self.assertEqual(self.l1[0]['status'],0)

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_with_episode(self):
		self.creation()
		self.l1.add(self.id1,season=1,epno=2)
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],1)
		self.assertEqual(self.l1[0]['episode'],2)
		self.assertEqual(self.l1[0]['keywords'],[])

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_with_episode_with_defaultKeywords(self):
		self.creation()
		self.l1.add(self.id1,season=1,epno=2,keywords=['niouf','niorf'])
		self.assertEqual(len(self.l1),1)
		self.assertEqual(self.l1[0]['season'],1)
		self.assertEqual(self.l1[0]['episode'],2)
		self.assertEqual(self.l1[0]['keywords'],['niouf','niorf'])

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_with_wrong_episode(self):
		self.creation()
		with self.assertRaises(Exception):
			self.l1.add(tvShow=self.id1,season=7,epno=2)
		self.assertEqual(len(self.l1),0)

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_already_in(self):
		self.creation()
		self.l1.add(self.id1)
		with self.assertRaises(Exception):
			self.l1.add(self.tvShow1)
		self.assertEqual(len(self.l1),1)

	@wwwoman.register_scenario("tvShowList1.json")
	def test_add_TvShow_multi(self):
		self.creation()
		self.l1.add(self.id1)
		self.l1.add(self.tvShow2)
		self.assertEqual(len(self.l1),2)

	@wwwoman.register_scenario("tvShowList1.json")
	def test_inList(self):
		self.creation()
		self.l1.add(self.tvShow1)
		self.assertTrue(self.l1.inList(self.id1))
		self.assertTrue(self.l1.inList(self.tvShow1))
		self.assertFalse(self.l1.inList(self.tvShow2))

	@wwwoman.register_scenario("tvShowList1.json")
	def test_getTvShow(self):
		self.creation()
		self.l1.add(self.tvShow1)
		self.assertEqual(self.l1.getTvShow(self.id1)['seriesid'],self.id1)
		self.assertIsNone(self.l1.getTvShow(self.id2))

	@wwwoman.register_scenario("tvShowList1.json")
	def test_delete(self):
		self.creation()
		self.l1.add(self.tvShow1)
		self.l1.add(self.tvShow2)
		self.assertTrue(self.l1.inList(self.id1))
		self.assertTrue(self.l1.inList(self.id2))
		self.assertTrue(os.path.isfile('{0}/banner_{1}.jpg'.format(self.tmpdirBanner,self.id1)))
		self.assertTrue(os.path.isfile('{0}/banner_{1}.jpg'.format(self.tmpdirBanner,self.id2)))
		self.l1.delete(self.id2)
		self.assertTrue(os.path.isfile('{0}/banner_{1}.jpg'.format(self.tmpdirBanner,self.id1)))
		self.assertFalse(os.path.isfile('{0}/banner_{1}.jpg'.format(self.tmpdirBanner,self.id2)))
		self.assertTrue(self.l1.inList(self.id1))
		self.assertFalse(self.l1.inList(self.id2))
		self.l1.add(self.tvShow2)
		self.l1.delete(self.id1)
		self.assertFalse(self.l1.inList(self.id1))
		self.assertTrue(self.l1.inList(self.id2))
		self.assertRaises(Exception,self.l1.delete,999)

	@wwwoman.register_scenario("tvShowList_complete.json")
	def test_update(self):
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		os.remove(tmpfile)
		shutil.copyfile('tests/tvShowList3.json',tmpfile)

		self.loadFullConfig()
		myList = tvShowList.tvShowList(banner_dir=self.tmpdirBanner,tvShows=tmpfile,verbosity=DEBUG_TVSHOWLIST)

		self.assertEqual(myList[0]['status'],0) # 321 S1E2 0 => 10
		self.assertEqual(myList[1]['status'],0) # 123 S1E1 0 => 22
		myList.update(downloader=self.downloader,transferer=self.transferer,searcher=self.torrentSearch,wait=True,force=True)
		self.assertEqual(myList[0]['status'],10) # 321 S1E2 0 => 10
		self.assertEqual(myList[1]['status'],22) # 123 S1E1 0 => 22

		myList[0].set(season=1,episode=1,status=10)
		myList[1].set(status=0)
		self.assertEqual(myList[0]['status'],10) # 321 S1E1 10 => 22
		self.assertEqual(myList[1]['status'],0) # 123 S1E1 0 => 30
		myList.update(wait=True,force=True)
		self.assertEqual(myList[0]['status'],22) # 321 S1E1 10 => 22
		self.assertEqual(myList[1]['status'],30) # 123 S1E1 0 => 30

		myList[1].set(season=1,episode=1,status=10)
		self.assertEqual(myList[0]['status'],22) # 321 S1E1 22 => 30
		self.assertEqual(myList[1]['status'],10) # 123 S1E1 10 => 30
		myList.update(wait=True,force=True)
		self.assertEqual(myList[0]['status'],30) # 321 S1E1 22 => 30
		self.assertEqual(myList[1]['status'],30) # 123 S1E1 10 => 30

		os.remove(tmpfile)

	@wwwoman.register_scenario("tvShowList1.json")
	def test_getValue(self):
		self.creation()
		self.l1.add(self.tvShow1)
		self.l1.add(self.tvShow2)
		self.assertEquals(self.l1.getValue()[0]['seriesid'],123)
		self.assertEquals(self.l1.getValue()[1]['seriesid'],321)
