#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import myTvDB
import wwwoman

DEBUG=True

class TestMyTvDB(unittest.TestCase):
	def setUp(self):
		wwwoman.wwwomanScenario.scenario_path = "tests/wwwoman/scenario"
		self.t = myTvDB.myTvDB(debug=DEBUG,cache=False)

	@wwwoman.register_scenario("thetvdb.json")
	def test_creation(self):
		self.assertIsInstance(self.t,myTvDB.myTvDB)

	@wwwoman.register_scenario("thetvdb.json")
	def test_search(self):
		self.assertIsInstance(self.t['TvShow1'],myTvDB.myShow)
		self.assertIsInstance(self.t['TvShow1'][1][1],myTvDB.myEpisode)


	@wwwoman.register_scenario("thetvdb.json")
	def test_lastAired(self):
		self.lastAired = self.t['TvShow1'].lastAired()
		self.assertIsInstance(self.lastAired,myTvDB.myEpisode)
		self.assertEqual(self.lastAired['firstaired'],'2010-05-23')

	@wwwoman.register_scenario("thetvdb.json")
	def test_nextAired_ok(self):
		self.nextAired = self.t[321].lastAired()
		self.assertIsInstance(self.nextAired,myTvDB.myEpisode)

	@wwwoman.register_scenario("thetvdb.json")
	def test_nextAired_ko(self):
		self.nextAired = self.t['TvShow1'].nextAired()
		self.assertIsNone(self.nextAired)

	@wwwoman.register_scenario("thetvdb.json")
	def test_nextAired_with_empty_season(self):
		self.nextAired = self.t[456].nextAired()
		self.assertIsNone(self.nextAired)

	@wwwoman.register_scenario("thetvdb.json")
	def test_next(self):
		self.assertIsNone(self.t['TvShow1'][1][2].next())
		self.assertIsInstance(self.t['TvShow1'][1][1].next(),myTvDB.myEpisode)

	@wwwoman.register_scenario("thetvdb.json")
	def test_next_wo_firstaired(self):
		self.assertIsNone(self.t[222][1][1].next())

	@wwwoman.register_scenario("thetvdb.json")
	def test_getEpisodesList(self):
		self.assertEquals(self.t[123].getEpisodesList(),{1:2})
		self.assertEquals(self.t[456].getEpisodesList(),{1:2})
