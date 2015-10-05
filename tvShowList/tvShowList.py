#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import JSAG
import myTvDB

class tvShowList(object):
	def __init__(self, l_tvShows=[]):
		self.schema = JSAG.loadParserFromFile("tvShowList/tvShowList.jschem")
		self.tvList = JSAG.JSAGdata(self.schema,value=l_tvShows)
		
	def loadFile(self,filename,path=[]):
		self.tvList.setFilename(filename,path=path)
		try:
			self.tvList.load()
		except IOError:
			print "File does not exist. Creating a new one"
			self.tvList.save()

	def __len__(self):
		if self is None:
			return 0
		else:
			return len(self.tvList)
			
	def _add_from_myTvDB(self,tvShow):
		if not isinstance(tvShow,myTvDB.myShow) and not isinstance(tvShow,myTvDB.myEpisode):
			raise TypeError("argument must be a myTvDB.myShow or myTvDB.myEpisode instance")
			
		if isinstance(tvShow,myTvDB.myEpisode):
			id = int(tvShow.get(u'id', 0))
			title = unicode(tvShow.get(u'seriesname', 0))
			season = int(tvShow.get(u'seasonnumber', 0))
			epno = int(tvShow.get(u'episodenumber', 0))
		else: #myShow instance
			id = int(tvShow['id'])
			title = unicode(tvShow['seriesname'])
			nextAired = tvShow.nextAired()
			if nextAired is None: # Broadcast achieved, schedule pilot
				season = 1
				epno = 1
			else:
				season = int(nextAired.get(u'seasonnumber', 0))
				epno = int(nextAired.get(u'episodenumber', 0))
		self.tvList.append({
							'id':int(id),
							'title':unicode(title),
							'status':0,
							'season':season,
							'episode':epno
							})
	
	def add(self,tvShow):
		if isinstance(tvShow,myTvDB.myShow) or isinstance(tvShow,myTvDB.myEpisode):
			self._add_from_myTvDB(tvShow)
		else:
			raise Exception("Not yet implemented")
				
