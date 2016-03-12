#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import json
import myTvDB
import logging
import JSAG3

class tvShowList(JSAG3.JSAG3):
	def __init__(self, l_tvShows=None,verbosity=False):
		if l_tvShows is None:
			l_tvShows = []
		JSAG3.JSAG3.__init__(self,
			id="tvShowList",
			schemaFile=None,
			optionsFile=None,
			dataFile=None,
			verbosity=verbosity
		)
		with open("tvShowSchedule/tvShowSchedule.jschem") as schema_file:    
			schema = json.load(schema_file)
		schema = {
					"type":"array",
					"items":schema
				}
		self.addSchema(schema)
		self.setValue(l_tvShows)
		self.tvdb = None
		
	def loadFile(self,filename,path=[]):
		self.addData(filename)
		logging.warning("[tvShowList] loadFile method is depreciate. Please use addData method")
		if path != []:
			logging.error("[tvShowList] loadFile method does not take path parameter anymore (JSAG3 limitation)")
		"""self.filename = filename
		self.path = path
		self.tvList.setFilename(filename,path=path)
		try:
			self.tvList.load()
		except IOError:
			print "File does not exist. Creating a new one"
			self.save(filename=filename,path=path)"""
			
	"""
	# Use method of parrent class JSAG3
	def save(self,filename=None,path=[]):
		if filename is not None:
			self.filename = filename
			self.path = path
		self.tvList.setFilename(filename,path=path)
		self.tvList.save()"""

	"""
	# Use method of parrent class JSAG3
	def __len__(self):
		if self is None:
			return 0
		else:
			return len(self.tvList)"""
			
	def _add_from_myTvDB(self,tvShow,season=None,epno=None):
		if not isinstance(tvShow,myTvDB.myShow) and not isinstance(tvShow,myTvDB.myEpisode):
			raise TypeError("argument must be a myTvDB.myShow or myTvDB.myEpisode instance")
			
		if isinstance(tvShow,myTvDB.myEpisode):
			id = int(tvShow.get(u'id', 0))
			title = unicode(tvShow.get(u'seriesname', 0))
			if not isinstance(season,int) and not isinstance(epno,int):
				season = int(tvShow.get(u'seasonnumber', 0))
				epno = int(tvShow.get(u'episodenumber', 0))
		else: #myShow instance
			id = int(tvShow['id'])
			title = unicode(tvShow['seriesname'])
			if not isinstance(season,int) and not isinstance(epno,int):
				nextAired = tvShow.nextAired()
				if nextAired is None: # Broadcast achieved, schedule pilot
					season = 1
					epno = 1
				else:
					season = int(nextAired.get(u'seasonnumber', 0))
					epno = int(nextAired.get(u'episodenumber', 0))
		if self.inList(id):
			raise Exception("{0} is already in the TvShow list")
			
		self._create_tvdb_api()
		try:
			self.tvdb[id][season][epno]
		except:
			raise Exception("S{0:02}E{1:02} does not exists for {2}".format())
		self.append({
					'seriesid':int(id),
					'title':unicode(title),
					'status':0,
					'season':season,
					'episode':epno
					})
	
	def add(self,tvShow,season=None,epno=None):
		if isinstance(tvShow,myTvDB.myShow) or isinstance(tvShow,myTvDB.myEpisode):
			self._add_from_myTvDB(tvShow,season=season,epno=epno)
		elif isinstance(tvShow,int):
			self._create_tvdb_api()
			self._add_from_myTvDB(self.tvdb[tvShow],season=season,epno=epno)
		else:
			raise Exception("Not yet implemented")
			
	def inList(self,tvShow):
		if isinstance(tvShow,myTvDB.myShow):
			id = int(tvShow.data['id'])
		elif isinstance(tvShow,int):
			id = tvShow
		else:
			raise Exception("Not yet implemented")
		return id in [show['seriesid'] for show in self.getValue()]
			
	def _create_tvdb_api(self):
		if self.tvdb is None:
			self.tvdb = myTvDB.myTvDB()
				
