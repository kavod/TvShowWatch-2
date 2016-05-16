#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import json
import datetime
import tzlocal
import threading
import myTvDB
import logging
import os
import cherrypy
import Downloader
import Notificator
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
		self.threads = []
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
		self.lock = threading.Lock()

		list.__init__(self,[])
		if isinstance(tvShows,basestring):
			self.addData(unicode(tvShows))
		else:
			for item in tvShows:
				self.add(item)

		self.downloader=None
		self.transferer=None
		self.searcher=None
		self.notificator=None

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
		self.threads = []

	# Load data from file
	def addData(self,dataFile):
		logging.debug("[tvShowList] Add data {0}".format(unicode(dataFile)))
		self.filename = unicode(dataFile)
		if self.isDataInitialized(self.filename):
			with open(self.filename) as data_file:
				fileContent = json.load(data_file)[self.id]
			for item in fileContent:
				if self.inList(item['seriesid']):
					tvShow = self.getTvShow(item['seriesid'])
					tvShow.setValue(item)
				else:
					tvShow = tvShowSchedule.tvShowSchedule(item['seriesid'],bannerDir=self.banner_dir,autoComplete=False,verbosity=self.verbosity)
					tvShow.setValue(item)
					self.add(tvShow)
			for key in [item['seriesid'] for item in self if not self.inList(item['seriesid'])]:
				self.delete(key)
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
					season = 0
					epno = 0
				else:
					season = int(nextAired.get(u'seasonnumber', 0))
					epno = int(nextAired.get(u'episodenumber', 0))
		if self.inList(id):
			raise Exception("{0} is already in the TvShow list".format(title))

		self._create_tvdb_api()
		if season * epno >0:
			try:
				self.tvdb[id][season][epno]
			except:
				raise Exception("S{0:02}E{1:02} does not exists for {2}".format(season,epno,title))

			self.append(
				tvShowSchedule.tvShowScheduleFromMyTvDBEpisode(
					self.tvdb[id][season][epno],
					bannerDir=self.banner_dir,
					verbosity=self.verbosity
				)
			)
		else:
			try:
				self.tvdb[id]
			except:
				raise Exception("Unable to reconize TV show {0} (ID: {1})".format(title,unicode(id)))
			self.append(
				tvShowSchedule.tvShowScheduleFromMyTvDB(
					self.tvdb[id],
					bannerDir=self.banner_dir,
					verbosity=self.verbosity
				)
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
		self.threads.append(None)

	def create_banner(self,seriesid,banner_url):
		banner_path = "{0}/self.banner_dir"

	def delete(self,tvShow):
		if isinstance(tvShow,int):
			try:
				index = next(index for (index, d) in enumerate(self) if d["seriesid"] == tvShow)
			except StopIteration:
				raise Exception("TvShow {0} not scheduled".format(unicode(tvShow).encode("utf8")))
			tvShow = self[index]
			tvShow.deleteBanner()
			if self.threads[index] is not None:
				self.threads[index].join()
			del(self[index])
			thread = self.threads[index]
			if thread is not None and thread.isAlive():
				thread.stop()
				thread.join()
			del(self.threads[index])
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

	def _setNotificator(self,notificator):
		if not isinstance(notificator,Notificator.Notificator):
			raise TypeError("parameter is not Notificator instance")
		self.notificator=notificator

	def _setTransferer(self,transferer):
		if not isinstance(transferer,Transferer.Transferer):
			raise TypeError("parameter is not Transferer instance")
		self.transferer=transferer

	def _setTorrentSearch(self,searcher):
		if not isinstance(searcher,torrentSearch.torrentSearch):
			raise TypeError("parameter is not torrentSearch instance")
		self.searcher=searcher

	def update(self,downloader=None,notificator=None,searcher=None,transferer=None,force=False,wait=False):
		if downloader is not None:
			self._setDownloader(downloader)
		if not isinstance(self.downloader,Downloader.Downloader):
			raise Exception("No downloader provided")

		if notificator is not None:
			self._setNotificator(notificator)

		if searcher is not None:
			self._setTorrentSearch(searcher)
		if not isinstance(self.searcher,torrentSearch.torrentSearch):
			raise Exception("No torrentSearch provided")

		if transferer is not None:
			self._setTransferer(transferer)
		if not isinstance(self.transferer,Transferer.Transferer):
			raise Exception("No transferer provided")

		# Update data from file
		#if self.filename is not None:
		#	self.addData(self.filename)

		for key,tvShow in enumerate(self):
			logging.info("[tvShowList] ******* UPDATE *******\nTvShow {0}".format(unicode(key)))
			if tvShow.downloader is None:
				tvShow._setDownloader(self.downloader)
			if tvShow.searcher is None:
				tvShow._setTorrentSearch(self.searcher)
			if tvShow.transferer is None:
				tvShow._setTransferer(self.transferer)
			if tvShow.notificator is None:
				tvShow._setNotificator(self.notificator)
			if force:
				now = datetime.datetime.now(tzlocal.get_localzone())
				tvShow.set(nextUpdate=now)
			if self.threads[key]:
				if self.threads[key].isAlive():
					logging.debug("[tvShowList] Thread alive for {0} ({1}).Skipping update".format(tvShow['info']['seriesname'],unicode(tvShow['seriesid'])))
				else:
					self.threads[key] = None
			else:
				self.threads[key] = threading.Thread(target=tvShow.update)
				self.threads[key].daemon = True
				self.threads[key].start()
				if wait:
					self.threads[key].join()
					self.threads[key] = None
		if self.filename is not None:
			self.lock.acquire()
			try:
				self.save()
			except Exception as e:
				self.lock.release()
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print(exc_type, fname, exc_tb.tb_lineno)
				raise e
			else:
				self.lock.release()

	def join(self):
		for thread in self.threads:
			if thread is not None and thread.isAlive():
				thread.join()

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
