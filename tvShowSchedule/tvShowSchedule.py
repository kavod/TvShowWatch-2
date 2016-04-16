#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import time
import datetime
import tzlocal
import json
import logging
import re
import urllib2
import myTvDB
import Downloader
import torrentSearch
import Transferer
import JSAG3

path = os.path.dirname(os.path.realpath(__file__))
with open(path + '/status.json') as data_file:    
	STATUS = json.load(data_file)
for key,item in STATUS.items():
	STATUS[int(key)] = item
	
def tvShowScheduleFromMyTvDB(tvShow, verbosity=False):
	if not isinstance(tvShow,myTvDB.myShow):
		raise TypeError("Incorrect argument: {0} ({1})".format(unicode(tvShow).encode('utf8'),type(tvShow)))
	next = tvShow.nextAired()
	if next is None:
		season = 1
		episode = 1
		status = 0
		nextUpdate = datetime.datetime.now(tzlocal.get_localzone()) + datetime.timedelta(minutes=2)
		downloader_id = ""
	else:
		season = int(next['seasonnumber'])
		episode = int(next['episodenumber'])
		status = 10
		nextUpdate = min(tzlocal.get_localzone().localize(datetime.datetime.strptime(next['firstaired'],'%Y-%m-%d')),datetime.datetime.now(tzlocal.get_localzone())+datetime.timedelta(days=7))
		downloader_id = ""
	return tvShowSchedule(
				seriesid=tvShow['id'],
				title=tvShow['seriesname'],
				season=season,
				episode=episode,
				status=status,
				nextUpdate=nextUpdate,
				downloader_id=downloader_id, 
				verbosity=verbosity
				)
	
def tvShowScheduleFromId(tvShow, verbosity=False):
	t = myTvDB.myTvDB()
	if not isinstance(tvShow,int):
		raise TypeError("Incorrect argument: {0}".format(unicode(tvShow).encode('utf8')))
	return tvShowScheduleFromMyTvDB(t[int(tvShow)], verbosity=verbosity)
	
def fakeTvDB(tvDB):
	global t
	if not isinstance(tvDB,myTvDB.myTvDB):
		raise TypeError("Incorrect argument: {0}".format(unicode(tvDB).encode('utf8')))
	t=tvDB

class tvShowSchedule(JSAG3.JSAG3):
	def __init__(self, seriesid, title, season=0, episode=0,status=0, nextUpdate=None, downloader_id = "", banner=None, banner_dir=".", dl_banner=False, verbosity=False):
		curPath = os.path.dirname(os.path.realpath(__file__))
		JSAG3.JSAG3.__init__(self,
			id="tvShow"+unicode(seriesid),
			schemaFile=curPath+"/tvShowSchedule.jschem",
			optionsFile=curPath+"/tvShowSchedule.jopt",
			dataFile=None,
			verbosity=verbosity
		)
		
		self.seriesid = int(seriesid)
		t = myTvDB.myTvDB()
		
		# Determine episode, status & nextUpdate
		if season*episode<1 and status != 90:
			next = t[self.seriesid].nextAired()
			if next is None:
				season = 1
				episode = 1
				status = 0
			else:
				season = int(next['seasonnumber'])
				episode = int(next['episodenumber'])
				status = 10
				nextUpdate = min(
					tzlocal.get_localzone().localize(datetime.datetime.strptime(next['firstaired'],'%Y-%m-%d')),
					datetime.datetime.now(tzlocal.get_localzone())+datetime.timedelta(days=7)
				)
				
		# Banner management
		if dl_banner:
			self.downloadedBanner = True
			if banner is None:
				if 'banner' in t[self.seriesid].data.keys():
					banner = t[self.seriesid].data['banner']
			if banner is not None:
				banner = re.sub(r'^(http:\/\/thetvdb\.com\/banners\/)(graphical\/[\w-]+\.\w+)$',r'\1_cache/\2',banner)
				extension = re.match(r'^http(s){0,1}:\/\/.*\.(\w+)$',banner)
				if extension is not None:
					update_file = True
					localfile = "{0}/banner_{1}.{2}".format(banner_dir,unicode(self.seriesid),extension.group(2))
					#Check if file is not outdated
					if os.path.isfile(localfile):
						now = datetime.datetime.now()
						last_mod = datetime.datetime.fromtimestamp(os.path.getmtime(localfile))
						refresh_rate = datetime.timedelta(days=30)
						if now - last_mod > refresh_rate:
							logging.debug("Banner is outdated. Download it again")
						else:
							update_file = False
					if update_file:
						with open(localfile,'wb') as f:
							f.write(urllib2.urlopen(banner).read())
							f.close()
					banner = localfile
		else:
			self.downloadedBanner = False
					
					
		if nextUpdate is None:
			nextUpdate = datetime.datetime.now(tzlocal.get_localzone()) + datetime.timedelta(minutes=2)
		self._set(seriesid=int(seriesid),title=unicode(title), season=season, episode=episode,status=status, nextUpdate=nextUpdate,downloader_id=downloader_id,banner=banner)
		self.downloader = None
		self.searcher = None
		
	def _set(self,seriesid=None,title=None,season=None,episode=None,status=None,nextUpdate=None, downloader_id = None,banner=None):
		logging.debug("[tvShowSchedule] TvShow will be updated. Old value:\n {0}".format(unicode(self.data)))
		value = {}
		value['seriesid'] = int(seriesid) if seriesid is not None else self.data['seriesid']
		value['title'] = unicode(title) if title is not None else self.data['title']
		if season is None or episode is None or (int(season) > 0) != (int(episode) > 0):
			value['season'] = self.data['season']
			value['episode'] = self.data['episode']
		else:
			value['season'] = int(season)
			value['episode'] = int(episode)
			
		if status is not None:
			if int(status) not in STATUS.keys():
				raise Exception("Incorrect status: {0}".format(unicode(status).encode('utf8')))
			value['status'] = int(status)
		else:
			value['status'] = self.data['status']
		if isinstance(nextUpdate,datetime.datetime):
			logging.debug("[tvShowSchedule] Next update is set to {0} ({1})".format(unicode(nextUpdate),type(nextUpdate)))
			if nextUpdate.tzinfo is None:
				nextUpdate = nextUpdate.replace(tzinfo=tzlocal.get_localzone())
				logging.debug("[tvShowSchedule] Applying timezone. Now next update is set to {0} ({1})".format(unicode(nextUpdate),type(nextUpdate)))
			value['nextUpdate'] = nextUpdate
		else:
			value['nextUpdate'] = self.data['nextUpdate']
			
		if isinstance(downloader_id,int) or isinstance(downloader_id,basestring):
			value['downloader_id'] = unicode(downloader_id)
		else:
			value['downloader_id'] = self.data['downloader_id']
		
		# Banner
		if 'info' not in value.keys():
			value['info'] = dict()
		
		if isinstance(banner,basestring):
			value['info']['banner_url'] = unicode(banner)
		else:
			if self.data is not None and 'info' in self.data.keys() and 'banner_url' in self.data['info']:
				value['info']['banner_url'] = self.data['info']['banner_url']
			
		self.data = JSAG3.updateData(self.data,value,self.schema)
		logging.debug("[tvShowSchedule] TvShow has been updated. New value:\n {0}".format(unicode(self.data)))
			
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
			
	def _setAchieved(self):
		nextUpdate = datetime.datetime.now(tzlocal.get_localzone()) + datetime.timedelta(days=30)
		self._set(season = 0,episode = 0,status = 90,nextUpdate=nextUpdate)
		
	def _setNotYetAired(self,episode):
		nextUpdate = min(tzlocal.get_localzone().localize(datetime.datetime.strptime(episode['firstaired'],'%Y-%m-%d')),datetime.datetime.now(tzlocal.get_localzone())+datetime.timedelta(days=7))
		self._set(season=int(episode['seasonnumber']),episode=int(episode['episodenumber']),status=10,nextUpdate=nextUpdate)
		
	def update(self,downloader=None,searcher=None,transferer=None,force=False):
		now = datetime.datetime.now(tzlocal.get_localzone())
		t = myTvDB.myTvDB()
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
			
		logging.debug("[tvShowSchedule] Next status scheduled on {0} ({2}). It is {1} ({3})".format(unicode(self['nextUpdate']),unicode(now),type(self['nextUpdate']),type(now)))
		if force or self['nextUpdate'] < now:
			logging.debug("[tvShowSchedule] Former status: {0}".format(self['status']))
			# Added
			if self['status'] == 0:
				# Episode identified
				if self['season'] * self['episode'] > 0:
					firstaired = tzlocal.get_localzone().localize(datetime.datetime.strptime(t[self['seriesid']][self['season']][self['episode']]['firstaired'],'%Y-%m-%d'))
					# Episode already aired, do next step
					if firstaired < now:
						self._set(status=20)
						self.update(force=True)
					else:
						# Episode not yet aired. Let's wait for it
						self._setNotYetAired(t[self['seriesid']][self['season']][self['episode']])
				# No episode identified
				else:
					tvShow = t[self['seriesid']]
					next = tvShow.nextAired()
					# No next episode. TV show is achieved
					if next is None:
						#self._setAchieved()
						self._set(status=0,season=1,episode=1)
						self.update(force=True)
					else:
						# Next episode now identified. Let's wait for it.
						self._setNotYetAired(next)
						
			# Not yet aired
			elif self['status'] == 10:
				firstaired = tzlocal.get_localzone().localize(datetime.datetime.strptime(t[self['seriesid']][self['season']][self['episode']]['firstaired'],'%Y-%m-%d'))
				# Episode now aired. Do next step
				if firstaired < now:
					self._set(status=20)
					self.update(force=True)
				# Episode still not aired. Let's wait until its broadcast
				else:
					self._setNotYetAired(t[self['seriesid']][self['season']][self['episode']])
			
			# Torrent watch
			elif self['status'] == 20:
				tor = self.searcher.search("{0} S{1:02}E{2:02}".format(self['title'],self['season'],self['episode']))
				# Torrent is found. Process download
				if tor is not None:
					tmpFile = self.searcher.download(tor)
					downloader_id=self.downloader.add_torrent(tmpFile)
					if downloader_id > 0:
						self._set(status=30,downloader_id=downloader_id)
				# In all case (torrent found or not) wait for 15min.
				nextUpdate = now+datetime.timedelta(minutes=15)
				self._set(nextUpdate=nextUpdate)
			
			# Download in progress
			elif self['status'] == 30:
				logging.debug("[tvShowSchedule] downloader_id is: {0}".format(self['downloader_id']))
				if self['downloader_id'] is not None:
					# Identifing status
					try:
						logging.debug("[tvShowSchedule] Downloader: {0}".format(self.downloader))
						status = self.downloader.get_status(self['downloader_id'])
						logging.debug("[tvShowSchedule] Get new status: {0}".format(status))
					except:
						logging.warning("[tvShowSchedule] Unable to retrieve status for: {0}".format(unicode(self['downloader_id'])))
						status = ''
					
					if status != '':
						# Status identified
						if status == "downloading":
							# Still downloading. Wait for 15min
							nextUpdate = now+datetime.timedelta(minutes=15)
							self._set(nextUpdate=nextUpdate)
						elif status == "seeding":
							# Download achieved. To be transfered.
							self._set(status=35)
							self.update(force=True)
					else:
						# Incorrect or missing torrent. Let's watch torrent again.
						self._set(status=20)
						self.update(force=True)
				else:
					# Incorrect or missing downloader identifier. Let's watch torrent again.
					self._set(status=20)
					self.update(force=True)
					
			# To be transfered
			elif self['status'] == 35:
				logging.debug("[tvShowSchedule] downloader_id is: {0}".format(self['downloader_id']))
				if self['downloader_id'] is not None:
					# Identifing status
					try:
						logging.debug("[tvShowSchedule] Downloader: {0}".format(self.downloader))
						status = self.downloader.get_status(self['downloader_id'])
						logging.debug("[tvShowSchedule] Get new status: {0}".format(status))
					except:
						status = ''
					
					if status != '':
						# Status identified
						if status == "downloading":
							# Still downloading. Download in progress. Wait for 15min
							nextUpdate = now+datetime.timedelta(minutes=15)
							self._set(status=30)
							self._set(nextUpdate=nextUpdate)
						elif status == "seeding":
							# Transfer torrent
							logging.debug("[tvShowSchedule] Transferer: {0}".format(self.transferer))
							files = self.downloader.get_files(self['downloader_id'])
							for myFile in files:
								self.transferer.transfer(myFile,delete_after=False)
							if self.transferer['delete_after']:
								#try:
								self.downloader.delete_torrent(self['downloader_id'])
								#except:
								#	logging.error("[tvShowSchedule] Unable to delete source file {0}. Ignoring".format(myFile))
								
							# Schedule next episode
							tvShow = t[self['seriesid']][self['season']][self['episode']]
							logging.debug("[tvShowSchedule] Current episode: {0}".format(unicode(tvShow)))
							next = tvShow.next()
							logging.debug("[tvShowSchedule] Next episode: {0}".format(unicode(next)))
							if next is None:
								self._setAchieved()
							else:
								self._set(season=next['seasonnumber'],episode=next['episodenumber'],status=0)
								self.update(force=True)
					else:
						# Incorrect or missing torrent. Let's watch torrent again.
						self._set(status=20)
						self.update(force=True)
					
				else:
					# Incorrect or missing downloader identifier. Let's watch torrent again.
					self._set(status=20)
					self.update(force=True)
				
			# Broadcast achieved
			elif self['status'] == 90:
				tvShow = t[self['seriesid']]
				next = tvShow.nextAired()
				if next is None:
					self._setAchieved()
				else:
					self._setNotYetAired(next)
					
	def pushTorrent(self,filename):
		if self['season'] * self['episode'] < 1:
			raise Exception("Season & episode are not set")
		pass
	
	def deleteBanner(self):
		if self.downloadedBanner:
			if self.data is not None and 'info' in self.data.keys() and 'banner_url' in self.data['info'].keys():
				if not re.match(r'^http(s){0,1}:\/\/.*\.(\w+)$',self.data['info']['banner_url']):
					os.remove(self.data['info']['banner_url'])
					del(self.data['info']['banner_url'])
