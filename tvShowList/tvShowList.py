#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import json
import myTvDB
import logging
import JSAG3
import Downloader
import Transferer
import torrentSearch
import tvShowSchedule

class tvShowList(JSAG3.JSAG3):
	def __init__(self, id="tvShowList",tvShows=None,verbosity=False):
		self.tvdb = None
		if tvShows is None:
			tvShows = []
		if (
			(
				isinstance(tvShows,list) 
				and not all(
						isinstance(item,myTvDB.myShow) 
						or isinstance(item,myTvDB.myEpisode) 
						or isinstance(item,tvShowSchedule.tvShowSchedule) 
						or isinstance(item,int)
						for item in tvShows
					)
			) 
			and not isinstance(tvShows,basestring)
		):
			raise Exception("tvShows parameter must be a basestring (for filename) or a list of myShow, myEpisode, tvShowSchedule or int values")
			
		self.verbosity = verbosity
		JSAG3.JSAG3.__init__(self,
			id=id,
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
		if isinstance(tvShows,basestring):
			self.addData(tvShows)
		else:
			for item in tvShows:
				self.add(item)
		#self.setValue(tvShows)
		self.downloader=None
		self.transferer=None
		self.searcher=None
		
	def loadFile(self,filename,path=[]):
		self.addData(filename)
		logging.warning("[tvShowList] loadFile method is depreciate. Please use addData method")
		if path != []:
			logging.error("[tvShowList] loadFile method does not take path parameter anymore (JSAG3 limitation)")
			
	def _add_from_tvShowSchedule(self,tvShow):
		if not isinstance(tvShow,tvShowSchedule.tvShowSchedule):
			raise TypeError("argument must be a tvShowSchedule instance")
		self.append(tvShow.getValue())
			
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
			raise Exception("{0} is already in the TvShow list".format(title))
			
		self._create_tvdb_api()
		try:
			self.tvdb[id][season][epno]
		except:
			raise Exception("S{0:02}E{1:02} does not exists for {2}".format())
		
		self.append(tvShowSchedule.tvShowSchedule(
			int(id), 
			unicode(title), 
			season=season, 
			episode=epno,
			status=0, 
			nextUpdate=None, 
			downloader_id = "", 
			verbosity=False).getValue()
		)
	
	def add(self,tvShow,season=None,epno=None):
		if isinstance(tvShow,myTvDB.myShow) or isinstance(tvShow,myTvDB.myEpisode):
			self._add_from_myTvDB(tvShow,season=season,epno=epno)
		elif isinstance(tvShow,int):
			self._create_tvdb_api()
			self._add_from_myTvDB(self.tvdb[tvShow],season=season,epno=epno)
		elif isinstance(tvShow,tvShowSchedule.tvShowSchedule):
			self._add_from_tvShowSchedule(tvShow)
		else:
			raise Exception("Add from {0} type is not yet implemented".format(type(tvShow)))
			
	def delete(self,tvShow):
		if isinstance(tvShow,int):
			try:
				index = next(index for (index, d) in enumerate(self.data) if d["seriesid"] == tvShow)
			except StopIteration:
				raise Exception("TvShow {0} not scheduled".format(unicode(tvShow).encode("utf8")))
			del(self.data[index])
		else:
			raise Exception("Delete from {0} type is not yet implemented".format(type(tvShow)))
			
	def inList(self,tvShow):
		if isinstance(tvShow,myTvDB.myShow):
			id = int(tvShow.data['id'])
		elif isinstance(tvShow,int):
			id = tvShow
		else:
			raise Exception("Not yet implemented")
		if self.data is None:
			return []
		return id in [show['seriesid'] for show in self.getValue()]
			
	def _create_tvdb_api(self):
		if self.tvdb is None:
			self.tvdb = myTvDB.myTvDB()
			
	def _setDownloader(self,downloader):
		if not isinstance(downloader,Downloader.Downloader):
			raise TypeError("parameter is not Downloader instance")
		self.downloader=downloader
		
	def _setTransferer(self,transferer):
		if not isinstance(transferer,Transferer.Transferer):
			raise TypeError("parameter is not Transferer instance")
		self.transferer=transferer
			
	def _setTorrentSearch(self,searcher):
		if not isinstance(searcher,torrentSearch.torrentSearch):
			raise TypeError("parameter is not torrentSearch instance")
		self.searcher=searcher
		
	def update(self,downloader=None,searcher=None,transferer=None,force=False):
		if downloader is not None:
			self._setDownloader(downloader)
		if not isinstance(self.downloader,Downloader.Downloader):
			raise Exception("No downloader provided")
			
		if searcher is not None:
			self._setTorrentSearch(searcher)
		if not isinstance(self.searcher,torrentSearch.torrentSearch):
			raise Exception("No torrentSearch provided")
			
		if transferer is not None:
			self._setTransferer(transferer)
		if not isinstance(self.transferer,Transferer.Transferer):
			raise Exception("No transferer provided")
		
		for key,item in enumerate(self.data):
			logging.info("[tvShowList] ******* UPDATE *******\nTvShow {0}".format(unicode(key)))
			tvShow = tvShowSchedule.tvShowSchedule(
				item['seriesid'], 
				item['title'], 
				item['season'], 
				item['episode'],
				item['status'], 
				item['nextUpdate'], 
				item['downloader_id'], 
				verbosity=self.verbosity)
			tvShow.update(downloader=self.downloader,searcher=self.searcher,transferer=self.transferer,force=force)
			self.data[key] = tvShow.getValue()
			
