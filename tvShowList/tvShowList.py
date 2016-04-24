#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import json
import datetime
import myTvDB
import logging
import os
import cherrypy
import Downloader
import Transferer
import torrentSearch
import tvShowSchedule

class tvShowList(list):
	def __init__(self, id="tvShowList",banner_dir=".",tvShows=None,verbosity=False):
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
			
		self.id = unicode(id)
		self.filename = None
		self.verbosity = verbosity
		self.banner_dir = unicode(banner_dir)
		self.root = Root()
		self.root.schema = Root()
		self.root.options = Root()
		self.root.data = Root()
		self.conf = {
			"/data".encode('utf8'): {
				'tools.caching.on': False
			}
		}
		
		list.__init__(self,[])
		if isinstance(tvShows,basestring):
			self.addData(unicode(tvShows))
		else:
			for item in tvShows:
				self.add(item)
				
		self.downloader=None
		self.transferer=None
		self.searcher=None

	# Check if filename is defined
	def checkCompleted(self):
		if self.filename is None:
			raise Exception("[tvShowList] Datafile has not been provided")
			
	# Control if file exists and is parsable with self.id key
	def isDataInitialized(self,dataFile):
		return isDataInitialized(self.id,dataFile)
	
	# Initialize file with empty array
	def initDataFile(self):
		self.checkCompleted()
		initDataFile(self.id,self.filename)
		
	# Load data from file	
	def addData(self,dataFile):
		logging.debug("[tvShowList] Add data {0}".format(unicode(dataFile)))
		self.filename = unicode(dataFile)
		if self.isDataInitialized(self.filename):
			with open(self.filename) as data_file:
				for item in json.load(data_file)[self.id]:
					tvShow = tvShowSchedule.tvShowScheduleFromId(item['seriesid'])
					value = tvShow.getValue(hidePassword=False)
					value.update(item)
					tvShow.setValue(value)
					self.add(tvShow)
		else:
			self.initDataFile()
		setattr(self.root.data,self.id.encode('utf8'),staticJsonFile(self.filename,self.id))
		
	def getValue(self,hidePassword=True):
		result = []
		for tvShow in self:
			result.append(tvShow.getValue(hidePassword))
		return result
			
	def _add_from_tvShowSchedule(self,tvShow):
		if not isinstance(tvShow,tvShowSchedule.tvShowSchedule):
			raise TypeError("argument must be a tvShowSchedule instance")
		self.append(tvShow)
			
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
			banner_dir = self.banner_dir,
			dl_banner=True,
			verbosity=False)
		)
		
	def save(self,filename=None):
		if filename is not None:
			self.filename = unicode(filename).encode('utf8')
		self.checkCompleted()
		content = getExistingData(self.filename)
		content[self.id] = []
		for tvShow in self:
			tvShow.isValid()
			content[self.id].append(tvShow.getValue(hidePassword=False))
		with open(self.filename, 'w') as outfile:
			json.dump(content, outfile,default=json_serial)
	
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
				index = next(index for (index, d) in enumerate(self) if d["seriesid"] == tvShow)
			except StopIteration:
				raise Exception("TvShow {0} not scheduled".format(unicode(tvShow).encode("utf8")))
			tvShow = self[index]
			tvShow.deleteBanner()
			del(self[index])
		else:
			raise Exception("Delete from {0} type is not yet implemented".format(type(tvShow)))
			
	def inList(self,tvShow):
		if isinstance(tvShow,myTvDB.myShow):
			id = int(tvShow.data['id'])
		elif isinstance(tvShow,int):
			id = tvShow
		else:
			raise Exception("Not yet implemented")
		if self is None:
			return []
		return id in [show['seriesid'] for show in self]
		
	def getTvShow(self,key):
		if self.inList(key):
			return (item for item in self if item['seriesid'] == key).next()
		else:
			return None
			
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
		
		for key,tvShow in enumerate(self):
			logging.info("[tvShowList] ******* UPDATE *******\nTvShow {0}".format(unicode(key)))
			tvShow.update(downloader=self.downloader,searcher=self.searcher,transferer=self.transferer,force=force)
		
	def getRoot(self,root=None):
		self.checkCompleted()
		if root is None:
			root = self.root
		else:
			if not hasattr(root, 'schema'):
				root.schema = Root()
			if not hasattr(root, 'options'):
				root.options = Root()
			if not hasattr(root, 'data'):
				root.data = Root()
			setattr(root.schema,self.id.encode('utf8'),getattr(self.root.schema,self.id.encode('utf8')))
			setattr(root.options,self.id.encode('utf8'),getattr(self.root.options,self.id.encode('utf8')))
			setattr(root.data,self.id.encode('utf8'),getattr(self.root.data,self.id.encode('utf8')))		
		return root
			
	def getConf(self,conf={}):
		self.checkCompleted()
		x = conf.copy()
		x.update(self.conf)
		return x
			
	# Depreciate
	def loadFile(self,filename,path=[]):
		self.addData(filename)
		logging.warning("[tvShowList] loadFile method is depreciate. Please use addData method")
		if path != []:
			logging.error("[tvShowList] loadFile method no longer takes path parameter anymore (JSAG3 limitation)")

def getExistingData(filename):
	filename = unicode(filename).encode('utf8')
	if os.path.isfile(filename):
		with open(filename) as fd:
			try:
				existingData = json.load(fd)
			except:
				raise Exception("Cannot parse {0}".format(filename))
		logging.debug("[tvShowList] Existing data:\n{0}".format(existingData))
		return existingData
	else:
		return dict()

def initDataFile(id,filename):
	id = unicode(id)
	filename = unicode(filename)
	logging.debug("[tvShowList] Initialize data '{0}' in {1}.".format(id,filename))
	newData = getExistingData(filename)
	newData[id] = []
		
	with open(filename, 'w') as outfile:
		json.dump(newData, outfile)

def isDataInitialized(id,dataFile):
	id = unicode(id)
	if os.path.isfile(dataFile):
		existingData = getExistingData(dataFile)
		if id in existingData.keys():
			logging.debug("[tvShowList] data file {0} already contains data.".format(unicode(dataFile)))
			return True
		else:
			logging.debug("[tvShowList] data file {0} does not contain data '{1}'. Existing data: {2}".format(unicode(dataFile),id,existingData.keys()))
			return False
	else:
		logging.debug("[tvShowList] data file {0} does not exist.".format(unicode(dataFile)))
		return False	
		
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")		

# Cherrypy classes
class Root(object):
	pass

class staticJsonFile(object):
	def __init__(self,filename,key=None):
		self.key = key
		self.filename = filename
		self.update()
			
	def update(self):
		if not hasattr(self,"lastModified") or os.path.getmtime(self.filename) != self.lastModified:
			with open(self.filename) as data_file:  
				self.data = json.load(data_file) 
				if self.key is not None: 
					self.data = self.data[self.key]
			self.lastModified = os.path.getmtime(self.filename)
			
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self):
		self.update()
		cherrypy.response.headers['Cache-Control'] = 'no-cache, must-revalidate'
		cherrypy.response.headers['Pragma'] = 'no-cache'
		cherrypy.lib.caching.expires(secs=0)
		return self.data
