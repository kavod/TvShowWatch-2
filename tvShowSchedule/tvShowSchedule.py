#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import time
import datetime
import dateutil
import tzlocal
import json
import logging
import re
import urllib2
import myTvDB
import Downloader
import torrentSearch
import Transferer
import Notificator
import ActivityLog
import JSAG3

path = os.path.dirname(os.path.realpath(__file__))
with open(path + '/status.json') as data_file:
	STATUS = json.load(data_file)
for key,item in STATUS.items():
	STATUS[int(key)] = item

def tvShowScheduleFromMyTvDB(tvShow,bannerDir=None, keywords=None, verbosity=False):
	if not isinstance(tvShow,myTvDB.myShow):
		raise TypeError("Incorrect argument: {0} ({1})".format(unicode(tvShow).encode('utf8'),type(tvShow)))
	tvShowSch = tvShowSchedule(
		seriesid=tvShow['id'],
		bannerDir=bannerDir,
		keywords=keywords,
		autoComplete=False,
		verbosity=verbosity)
	if 'overview' in tvShow.data.keys() and tvShow['overview'] is not None:
		overview = tvShow['overview']
	else:
		overview = ''
	tvShowSch.set(
		info={
			"seriesname":tvShow['seriesname'],
			"overview":overview,
			'banner':('banner' in tvShow.data.keys() and tvShow['banner'] is not None)
		},
		season=0,
		episode=0,
		status=0,
		nextUpdate=datetime.datetime.now(tzlocal.get_localzone()) + datetime.timedelta(minutes=2),
		downloader_id="",
		autoComplete=True
	)
	return tvShowSch

def tvShowScheduleFromMyTvDBEpisode(episode,bannerDir=None, keywords=None, verbosity=False):
	if not isinstance(episode,myTvDB.myEpisode):
		raise TypeError("Incorrect argument: {0} ({1})".format(unicode(episode).encode('utf8'),type(episode)))
	tvShow = myTvDB.myTvDB()[int(episode.get(u'seriesid', 0))]
	tvShowSch = tvShowScheduleFromMyTvDB(tvShow,bannerDir=bannerDir, keywords=keywords,verbosity=verbosity)
	tvShowSch.set(
		info={
			"firstaired":episode.get(u'firstaired', 0)
		},
		season=int(episode.get(u'seasonnumber', 0)),
		episode=int(episode.get(u'episodenumber', 0)),
		status=0,
		autoComplete=True
	)
	return tvShowSch

def tvShowScheduleFromId(tvShow,bannerDir=None, keywords=None, verbosity=False):
	t = myTvDB.myTvDB()
	if not isinstance(tvShow,int):
		raise TypeError("Incorrect argument: {0}".format(unicode(tvShow).encode('utf8')))
	return tvShowScheduleFromMyTvDB(t[int(tvShow)],bannerDir=bannerDir, keywords=keywords,verbosity=verbosity)

def fakeTvDB(tvDB):
	global t
	if not isinstance(tvDB,myTvDB.myTvDB):
		raise TypeError("Incorrect argument: {0}".format(unicode(tvDB).encode('utf8')))
	t=tvDB

class tvShowSchedule(JSAG3.JSAG3):
	def __init__(self,seriesid,bannerDir=None,autoComplete=True,keywords=None,verbosity=False):
		self.seriesid = int(seriesid)
		self.verbosity = verbosity
		curPath = os.path.dirname(os.path.realpath(__file__))
		JSAG3.JSAG3.__init__(self,
			id="tvShow"+unicode(self.seriesid),
			schemaFile=curPath+"/tvShowSchedule.jschem",
			optionsFile=curPath+"/tvShowSchedule.jopt",
			dataFile=None,
			verbosity=verbosity
		)
		self._setLogger(self['seriesid'] if 'seriesid' in self.keys() else None)
		if bannerDir is not None and not isinstance(bannerDir,basestring):
			raise ValueError("bannerDir must be string or None, not {0}".format(type(bannerDir)))
		keywords = self.setDefaultKeywords(keywords,[])

		self.bannerDir = bannerDir
		self.downloader = None
		self.notificator = None
		self.transferer = None
		self.searcher = None
		self.activitylog = None
		self.set(keywords=keywords,autoComplete=autoComplete)
		self.logger.info("Creation of tvShowSchedule (seriesid: {0})".format(unicode(seriesid)))

	def set(
			self,
			season=None,
			episode=None,
			status=None,
			nextUpdate=None,
			downloader_id=None,
			pattern=None,
			info=None,
			emails=None,
			keywords=None,
			autoComplete=True
			):
		self.logger.debug("[TvShowSchedule] set method called")
		v2MinutesAfter = datetime.datetime.now(tzlocal.get_localzone()) + datetime.timedelta(minutes=2)

		# Initialization
		if self.data is None:
			self.data = {
							"season":0,
							"episode":0,
							"status":0,
							"nextUpdate":v2MinutesAfter,
							"seriesid":self.seriesid,
							"downloader_id":"",
							"info":{},
							"emails":[],
							"keywords":[]
						}

		# Status
		if status is not None:
			if isinstance(status,int):
				if status not in STATUS.keys():
					raise Exception("Incorrect status: {0}".format(unicode(status).encode('utf8')))
			else:
				raise ValueError("Status must be an integer, not {0}".format(type(status)))
			oldStatus = self['status']
			self['status'] = status

		# Season/Episode
		if (season is None) != (episode is None):
			season = None
			episode = None

		if season is not None:
			if isinstance(season,int) and isinstance(episode,int) and season >= 0 and episode >= 0:
				if season * episode < 1:
					season = 0
					episode = 0
					if self['status'] not in [ 0, 90 ]:
						self['status'] = 0
				self['season'] = season
				self['episode'] = episode
				if 'infoUpdate' in self['info'].keys():
					del(self['info']['infoUpdate'])
				if status is None:
					self['status'] = 0
			else:
				raise ValueError("Season & Episode must be positive integers. Got: {0} and {1}".format(type(season),type(episode)))

		# Add entry in activityLog
		if self.activitylog is not None and status is not None:
			self.activitylog.add_entry(
				self.seriesid,
				self['season'],
				self['episode'],
				oldStatus,
				self['status'],
				"info"
			)

		# NextUpdate
		if nextUpdate is not None:
			if isinstance(nextUpdate,basestring):
				nextUpdate = dateutil.parser.parse(nextUpdate)
			if isinstance(nextUpdate,datetime.datetime):
				if nextUpdate.tzinfo is None or nextUpdate.tzinfo.utcoffset(nextUpdate) is None:
					nextUpdate = tzlocal.get_localzone().localize(nextUpdate)
				self['nextUpdate'] = nextUpdate
			else:
				raise ValueError("nextUpdate must be a datetime, not {0}".format(type(nextUpdate)))

		# Downloader_id
		if downloader_id is not None:
			if isinstance(downloader_id,basestring) or isinstance(downloader_id,int):
				self['downloader_id'] = unicode(downloader_id)
			else:
				raise ValueError("downloader_id must be a string, not {0}".format(type(downloader_id)))

		# Pattern
		if pattern is not None:
			if isinstance(pattern,basestring) or isinstance(pattern,int):
				self['pattern'] = unicode(pattern)
			else:
				raise ValueError("pattern must be a string, not {0}".format(type(pattern)))

		# Info
		if info is not None:
			if isinstance(info,dict):
				if 'seriesname' in info.keys() and info['seriesname'] is not None:
					if isinstance(info['seriesname'],basestring):
						self['info']['seriesname'] = unicode(info['seriesname'])
					else:
						raise ValueError("info.seriesname must be a string, not {0}".format(type(info['seriesname'])))
				if 'overview' in info.keys() and info['overview'] is not None:
					if isinstance(info['overview'],basestring):
						self['info']['overview'] = unicode(info['overview'])
					else:
						raise ValueError("info.overview must be a string, not {0}".format(type(info['overview'])))
				if 'firstaired' in info.keys():
					if info['firstaired'] is not None:
						firstaired = info['firstaired']
						if isinstance(firstaired,basestring):
							firstaired = dateutil.parser.parse(firstaired)
						if isinstance(firstaired,datetime.datetime):
							if firstaired.tzinfo is None or firstaired.tzinfo.utcoffset(firstaired) is None:
								firstaired = tzlocal.get_localzone().localize(firstaired)
							self['info']['firstaired'] = firstaired
						else:
							raise ValueError("info.firstaired must be a datetime, not {0}".format(type(firstaired)))
					else:
						if 'firstaired' in self['info'].keys():
							del(self['info']['firstaired'])
				if 'infoUpdate' in info.keys() and info['infoUpdate'] is not None:
					infoUpdate = info['infoUpdate']
					if isinstance(infoUpdate,basestring):
						infoUpdate = dateutil.parser.parse(infoUpdate)
					if isinstance(infoUpdate,datetime.datetime):
						if infoUpdate.tzinfo is None or infoUpdate.tzinfo.utcoffset(infoUpdate) is None:
							infoUpdate = tzlocal.get_localzone().localize(infoUpdate)
						self['info']['infoUpdate'] = infoUpdate
					else:
						raise ValueError("info.infoUpdate must be a datetime, not {0}".format(type(infoUpdate)))
				if 'banner' in info.keys() and info['banner'] is not None:
					if isinstance(info['banner'],bool):
						self['info']['banner'] = info['banner']
					else:
						raise TypeError("info.banner must be a boolean, not {0}".format(type(info['banner'])))
				if 'episodesList' in info.keys() and info['episodesList'] is not None:
					if isinstance(info['episodesList'],dict):
						arrList = [0]
						for key in range(1,99):
							if key in info['episodesList'].keys():
								arrList.append(info['episodesList'][key])
							else:
								break
						info['episodesList'] = arrList
					if isinstance(info['episodesList'],list):
						info['episodesList'][0] = 0
						if all(isinstance(item,int) for item in info['episodesList']):
							self['info']['episodesList'] = info['episodesList']
						else:
							raise TypeError("info.episodesList must be an array of integers. Got {0}".format(unicode(info['episodesList'])))
					else:
						raise TypeError("info.episodesList must be an array of integers. Not {0}".format(type(info['episodesList'])))
			else:
				raise ValueError("info must be a dict, not {0}".format(type(info)))

		# Emails
		if emails is not None:
			if isinstance(emails,list) and all(isinstance(item,basestring) for item in emails):
				self['emails'] = emails
			else:
				raise ValueError("emails must be an array of string (with email format). Got {0}".format(type(emails)))

		# Keywords
		keywords = self.setDefaultKeywords(keywords,None)
		if keywords is not None:
			self['keywords'] = keywords

		self.setDefault()
		if autoComplete:
			self.updateInfo(force=False)

		if self.dataFile is not None:
			self.save()

	def setDefault(self):
		self.logger.debug("setDefault method called")
		v2MinutesAfter = datetime.datetime.now(tzlocal.get_localzone()) + datetime.timedelta(minutes=2)
		self.data.setdefault('season',0)
		self.data.setdefault('episode',0)
		self.data.setdefault('status',0)
		self.data.setdefault('season',v2MinutesAfter)
		self.data.setdefault('downloader_id','')
		self.data.setdefault('info',{})
		self.data.setdefault('emails',[])
		self.data.setdefault('keywords',[])
		if 'pattern' not in self.data.keys() or self['pattern'] is None:
			if 'seriesname' in self['info'].keys():
				self['pattern'] = self['info']['seriesname'].lower()

	@staticmethod
	def setDefaultKeywords(keywords,default):
		if keywords is None:
			return default
		else:
			if isinstance(keywords,list) and all(isinstance(item,basestring) for item in keywords):
				return keywords
			else:
				raise ValueError("keywords must be an array of string. Got {0}".format(type(keywords)))

	def updateInfo(self,force=False):
		self.logger.debug("[TvShowSchedule] updateInfo method called")
		v30DaysAgo = datetime.datetime.now(tzlocal.get_localzone()) - datetime.timedelta(days=30)
		if force:
			self['info']['infoUpdate'] = v30DaysAgo
		# If update is forced or info is indicated and newer than 30 days ago
		if force or self['info'].setdefault('infoUpdate',v30DaysAgo) <= v30DaysAgo:
			t = myTvDB.myTvDB()
			if 'overview' in t[self.seriesid].data.keys() and t[self.seriesid].data['overview'] is not None:
				overview = t[self.seriesid].data['overview']
			else:
				overview = ""
			bannerAvailable = (
				self.bannerDir is not None
				and 'banner' in t[self.seriesid].data
				and t[self.seriesid].data['banner'] is not None
			)
			episodesList = t[self.seriesid].getEpisodesList()
			arrList = [0]
			for key in range(1,99):
				if key in episodesList.keys():
					arrList.append(episodesList[key])
				else:
					break
			episodesList = arrList
			info={
				'seriesname':t[self.seriesid].data['seriesname'],
				'overview':overview,
				'infoUpdate':datetime.datetime.now(tzlocal.get_localzone()),
				'banner': bannerAvailable,
				'episodesList':episodesList
			}
			self.set(info=info,autoComplete=False)
			if bannerAvailable and not self.isBannerUpdated():
				self.updateBanner(t[self.seriesid].data['banner'])

			if self['season'] * self['episode'] > 0:
				try:
					t[self.seriesid][self['season']][self['episode']]
				except:
					self.logger.error("[tvShowSchedule] {0} S{1:02}E{2:02} does not exist. Reset to next episode"
						.format(self.seriesid,self['season'],self['episode']))
					self.set(season=0,episode=0,status=0,autoComplete=True)
					return
				episodeData = t[self.seriesid][self['season']][self['episode']]
				firstaired = episodeData['firstaired']
				if isinstance(firstaired,basestring):
					firstaired = dateutil.parser.parse(firstaired)
				if firstaired is None:
					self.logger.error("[tvShowSchedule] No firstaired for {0}".format(unicode(firstaired)))
					raise Exception("No firstaired for {0}".format(unicode(firstaired)))
				if firstaired.tzinfo is None or firstaired.tzinfo.utcoffset(firstaired) is None:
					firstaired = tzlocal.get_localzone().localize(firstaired)
				info['firstaired'] = firstaired
			self.set(info=info,autoComplete=False)
		self.setDefault()
		self.logger.debug("[tvShowSchedule] TvShow has been updated. New value:\n {0}".format(unicode(self.data)))

	def isInfoUpdated(self):
		v30DaysAgo = datetime.datetime.now(tzlocal.get_localzone()) - datetime.timedelta(days=30)
		if 'seriesname' not in self['info']:
			return False
		if 'overview' not in self['info']:
			return False
		if 'infoUpdate' not in self['info']:
			return False
		if 'banner' not in self['info']:
			return False
		if 'episodesList' not in self['info']:
			return False
		if not self.isBannerUpdated():
			return False
		if self['season'] * self['episode'] > 0 and 'firstaired' not in self['info']:
			return False
		if self['info']['infoUpdate'] < v30DaysAgo:
			return False
		return True

	def bannerPath(self):
		if self.bannerDir is None:
			raise Exception("No bannerDir")
		return "{0}/banner_{1}.jpg".format(self.bannerDir,unicode(self.seriesid))

	def isBannerUpdated(self):
		v30DaysAgo = datetime.datetime.now(tzlocal.get_localzone()) - datetime.timedelta(days=30)
		if self['info']['banner'] and self.bannerDir is not None:
			localfile = self.bannerPath()
			if os.path.isfile(localfile):
				last_mod = datetime.datetime.fromtimestamp(os.path.getmtime(localfile))
				last_mod = last_mod.replace(tzinfo=tzlocal.get_localzone())
				if os.path.isfile(localfile):
					self.logger.debug(
						"Banner {2} last modification is {0}. Allowed age is {1}"
						.format(
							unicode(last_mod),
							unicode(v30DaysAgo),
							localfile
						)
					)
					if last_mod < v30DaysAgo:
						return False
				else:
					return False
			else:
				return False
		return True

	def updateBanner(self,url):
		localfile = self.bannerPath()
		url = re.sub(r'^(http:\/\/thetvdb\.com\/banners\/)(graphical\/[\w-]+\.\w+)$',r'\1_cache/\2',url)
		with open(localfile,'wb') as f:
			f.write(urllib2.urlopen(url).read())
			f.close()

	def deleteBanner(self):
		if (self.bannerDir is not None and self['info']['banner']):
			try:
				os.remove(self.bannerPath())
			except:
				pass
			self.data['info']['banner'] = False

	def setValue(self,value):
		JSAG3.JSAG3.setValue(self,value)
		self.setDefault()
		if not self.isInfoUpdated():
			self.updateInfo(force=True)
		self.logger.debug("[tvShowSchedule] TvShow has been updated. New value:\n {0}".format(unicode(self.data)))

	def _setDownloader(self,downloader,mandatory=True):
		if downloader is not None:
			if not isinstance(downloader,Downloader.Downloader):
				raise TypeError("parameter is not Downloader instance")
			self.downloader=downloader
		if mandatory and not isinstance(self.downloader,Downloader.Downloader):
			raise Exception("No downloader provided")

	def _setNotificator(self,notificator,mandatory=False):
		if notificator is not None:
			if not isinstance(notificator,Notificator.Notificator):
				raise TypeError("parameter is not Notificator instance")
			self.notificator=notificator
		if mandatory and not isinstance(notificator,Notificator.Notificator):
			raise Exception("No notificator provided")

	def _setTransferer(self,transferer,mandatory=True):
		if transferer is not None:
			if not isinstance(transferer,Transferer.Transferer):
				raise TypeError("parameter is not Transferer instance")
			self.transferer=transferer
		if mandatory and not isinstance(transferer,Transferer.Transferer):
			raise Exception("No transferer provided")

	def _setTorrentSearch(self,searcher,mandatory=True):
		if searcher is not None:
			if not isinstance(searcher,torrentSearch.torrentSearch):
				raise TypeError("parameter is not torrentSearch instance")
			self.searcher = searcher
		if mandatory and not isinstance(self.searcher,torrentSearch.torrentSearch):
			raise Exception("No torrentSearch provided")

	def _setActivityLog(self,activitylog,mandatory=False):
		if activitylog is not None:
			if not isinstance(activitylog,ActivityLog.ActivityLog):
				raise TypeError("parameter is not ActivityLog instance")
			self.activitylog=activitylog
		if mandatory and not isinstance(self.activitylog,ActivityLog.ActivityLog):
			raise Exception("No ActivityLog provided")

	def _setAchieved(self):
		info = {"firstaired":None}
		nextUpdate = datetime.datetime.now(tzlocal.get_localzone()) + datetime.timedelta(days=30)
		self.set(season = 0,episode = 0,info = info, status = 90,nextUpdate=nextUpdate)

	def _setNotYetAired(self,episode):
		nextUpdate = min(tzlocal.get_localzone().localize(datetime.datetime.strptime(episode['firstaired'],'%Y-%m-%d')),datetime.datetime.now(tzlocal.get_localzone())+datetime.timedelta(days=7))
		self.set(season=int(episode['seasonnumber']),episode=int(episode['episodenumber']),status=10,nextUpdate=nextUpdate)

	def get_progression(self,downloader=None):
		if downloader is not None:
			self._setDownloader(downloader)
		if not isinstance(self.downloader,Downloader.Downloader):
			raise Exception("No downloader provided")

		if self['status'] not in [30,35]:
			return 0

		if self['downloader_id'] is None:
			# Incorrect or missing downloader identifier.
			self.logger.warning("Unable to determine slot. Push the status to 20")
		else:
			try:
				self.logger.debug("Downloader: {0}".format(self.downloader))
				progression = self.downloader.get_progression(self['downloader_id'])
				self.logger.debug("Get new progression: {0}".format(unicode(progression)))
				return progression
			except Exception as e:
				self.logger.warning(
					"Unable to retrieve progression for slot N°{0} ({1})"
					.format(unicode(self['downloader_id']),unicode(e))
				)

			# Something went wrong... Let's restart download
			#self.set(status=20)


	def update(self,downloader=None,searcher=None,transferer=None,notificator=None,activitylog=None,force=False):
		now = datetime.datetime.now(tzlocal.get_localzone())
		try:
			t = myTvDB.myTvDB()
		except:
			self.logger.error("Offline mode. Update canceled")
			return

		self._setDownloader(downloader)
		self._setTorrentSearch(searcher,mandatory=False)
		self._setTransferer(transferer,mandatory=False)
		self._setNotificator(notificator,mandatory=False)
		self._setActivityLog(activitylog,mandatory=False)

		self.logger.debug("Next status scheduled on {0} ({2}). It is {1} ({3})".format(unicode(self['nextUpdate']),unicode(now),type(self['nextUpdate']),type(now)))
		if not self.isInfoUpdated():
			self.updateInfo(force=True)

		try:
			self['nextUpdate'] < now
		except:
			raise Exception(self)
		if force or self['nextUpdate'] < now:
			self.logger.debug("Former status: {0}".format(self['status']))
			# Added
			if self['status'] == 0:
				# Episode identified
				if self['season'] * self['episode'] > 0:
					firstaired = tzlocal.get_localzone().localize(datetime.datetime.strptime(t[self['seriesid']][self['season']][self['episode']]['firstaired'],'%Y-%m-%d'))
					# Episode already aired, do next step
					if firstaired < now:
						self.set(status=20)
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
						self._setAchieved()
					else:
						# Next episode now identified. Let's wait for it.
						self._setNotYetAired(next)

			# Not yet aired
			elif self['status'] == 10:
				firstaired = tzlocal.get_localzone().localize(datetime.datetime.strptime(t[self['seriesid']][self['season']][self['episode']]['firstaired'],'%Y-%m-%d'))
				# Episode now aired. Do next step
				if firstaired < now:
					self.set(status=20)
					self.update(force=True)
				# Episode still not aired. Let's wait until its broadcast
				else:
					self._setNotYetAired(t[self['seriesid']][self['season']][self['episode']])

			# Torrent needed
			elif self['status'] == 20:
				self._setTorrentSearch(searcher)
				if 'providers' in self.searcher.keys() and len(self.searcher['providers'])>0:
					self.logger.debug(
						"{0} torrent provider(s) found"
						.format(unicode(len(self.searcher['providers']))))
					self.set(status=22,nextUpdate=now)
				else:
					self.logger.debug("No torrent provider found")
					self.set(status=21,nextUpdate=now)
				self.update(force=True)

			# Torrent required from user
			elif self['status'] == 21:
				if 'providers' in self.searcher.keys() and len(self.searcher['providers'])>0:
					self.logger.debug(
						"{0} torrent provider(s) found"
						.format(unicode(len(self.searcher['providers']))))
					self.set(status=22,nextUpdate=now)
					self.update(force=True)
				# else... just waiting
				nextUpdate = now+datetime.timedelta(minutes=5)
				self.set(nextUpdate=nextUpdate)

			# Torrent watch from torrent provider
			elif self['status'] == 22:
				self._setTorrentSearch(searcher)
				if 'providers' not in self.searcher.keys() or len(self.searcher['providers'])<1:
					self.set(status=21,nextUpdate=now)
				if 'keywords' not in self.keys() or len(self['keywords']) < 1:
					# No keywords
					keywords = ['']
				else:
					keywords = self['keywords']
				for keyword in keywords:
					search_pattern = "{0} S{1:02}E{2:02} {3}".format(self['pattern'],self['season'],self['episode'],keyword)
					tor = self.searcher.search(search_pattern)
					# Torrent is found. Process download
					self.logger.debug("Torrent is found with pattern '{0}'. Process download".format(search_pattern))
					if tor is not None:
						tmpFile = self.searcher.download(tor)
						self.logger.debug("Torrent downloaded at {0}.".format(tmpFile))
						try:
							downloader_id=unicode(self.downloader.add_torrent(tmpFile))
							if downloader_id != '-1':
								self.set(status=30,downloader_id=downloader_id,nextUpdate=now)
								self.update(force=True)
								return
							else:
								self.logger.error("Unknown error when adding torrent")
						except Downloader.DownloaderConnectionError:
							# Connection error with downloader. Waiting for 5mins
							self.logger.error("Connection error with downloader. Waiting for 5mins")
							nextUpdate = now+datetime.timedelta(minutes=5)
							self.set(nextUpdate=nextUpdate)
							return
						except Downloader.DownloaderCorruptedTorrent:
							# Torrent found seems corrupted. Waiting for 5mins
							self.logger.error("Torrent found seems corrupted. Waiting for 5mins")
							nextUpdate = now+datetime.timedelta(minutes=5)
							self.set(nextUpdate=nextUpdate)
							return

				# If torrent not found wait for 15min.
				self.logger.debug("Torrent not found")
				nextUpdate = now+datetime.timedelta(minutes=15)
				self.set(nextUpdate=nextUpdate)

			# Download in progress
			elif self['status'] == 30:
				self.logger.debug("downloader_id is: {0}".format(self['downloader_id']))
				if self['downloader_id'] is not None:
					# Identifing status
					try:
						self.logger.debug("[tvShowSchedule] Downloader: {0}".format(self.downloader))
						status = self.downloader.get_status(self['downloader_id'])
						self.logger.debug("[tvShowSchedule] Get new status: {0}".format(status))
					except:
						self.logger.warning("[tvShowSchedule] Unable to retrieve status for: {0}".format(unicode(self['downloader_id'])))
						status = ''

					if status != '':
						# Status identified
						if status == "downloading":
							# Still downloading. Wait for 15min
							nextUpdate = now+datetime.timedelta(minutes=15)
							self.set(nextUpdate=nextUpdate)
						elif status == "seeding":
							# Download achieved. To be transfered.
							self.set(status=35)
							self.update(force=True)
						elif status in ['paused','stopped']:
							# Download paused. Restarting.
							self.set(status=33)
							self.update(force=True)
						else:
							# Unhandled status
							nextUpdate = now+datetime.timedelta(minutes=15)
							self.set(nextUpdate=nextUpdate)
					else:
						# Incorrect or missing torrent. Let's watch torrent again.
						self.set(status=20)
						self.update(force=True)
				else:
					# Incorrect or missing downloader identifier. Let's watch torrent again.
					self.logger.error("Unable to determine slot. Push the status to 20")
					self.set(status=20)
					self.update(force=True)

			# Paused
			elif self['status'] == 33:
				self.logger.debug("downloader_id is: {0}".format(self['downloader_id']))
				if self['downloader_id'] is not None:
					self.logger.debug("Starting on {0}".format(self.downloader))
					self.downloader.start_torrent(self['downloader_id'])
					nextUpdate = now+datetime.timedelta(minutes=15)
					self.set(status=30,nextUpdate=nextUpdate)
				else:
					self.logger.error("Unable to determine slot. Push the status to 20")
					self.set(status=20)
					self.update(force=True)


			# To be transfered
			elif self['status'] == 35:
				self.logger.debug("downloader_id is: {0}".format(self['downloader_id']))
				if self['downloader_id'] is not None:
					# Identifing status
					try:
						self.logger.debug("Downloader: {0}".format(self.downloader))
						status = self.downloader.get_status(self['downloader_id'])
						self.logger.debug("Get new status: {0}".format(status))
					except:
						status = ''

					if status != '':
						# Status identified
						if status == "downloading":
							# Still downloading. Download in progress. Wait for 15min
							nextUpdate = now+datetime.timedelta(minutes=15)
							self.set(status=30,nextUpdate=nextUpdate)
						elif status == "seeding":
							# Transfer torrent
							self.downloadTorrent()
					else:
						# Incorrect or missing torrent. Let's watch torrent again.
						self.set(status=20)
						self.update(force=True)

				else:
					# Incorrect or missing downloader identifier. Let's watch torrent again.
					self.set(status=20)
					self.update(force=True)

			# Download completed
			elif self['status'] == 39:
				notifContent = "{0} S{1:02}E{2:02} has been downloaded.\n".format(self['info']['seriesname'],self['season'],self['episode'])

				# Schedule next episode
				tvShow = t[self['seriesid']][self['season']][self['episode']]
				self.logger.debug("[tvShowSchedule] Current episode: {0}".format(unicode(tvShow)))
				next = tvShow.next()
				self.logger.debug("[tvShowSchedule] Next episode: {0}".format(unicode(next)))
				if next is None:
					self._setAchieved()
					notifContent += "Unfortunatly, for moment, it is the last episode scheduled for this TV show :("
				else:
					self.set(season=int(next['seasonnumber']),episode=int(next['episodenumber']),status=0)
					self.update(force=True)
					notifContent += "The next episode (S{0:02}E{1:02}) is expected on {2}".format(self['season'],self['episode'],self['info']['firstaired'])
				if self.notificator is not None:
					self.notificator.send("Download completed!",notifContent,self['emails'])

			# Broadcast achieved
			elif self['status'] == 90:
				tvShow = t[self['seriesid']]
				next = tvShow.nextAired()
				if next is None:
					self._setAchieved()
				else:
					self._setNotYetAired(next)
			else:
				# Incorrect or missing status. Put status to 0
				self.set(status=0)
				self.update(force=True)

	def downloadTorrent(self):
		self._setTransferer(self.transferer,mandatory=True)
		# Transfer torrent
		self.logger.debug("Transferer: {0}".format(self.transferer))
		files = self.downloader.get_files(self['downloader_id'])
		if 'enable' in self.transferer.keys() and self.transferer['enable']:
			for myFile in files:
				rtn = self.transferer.transfer(myFile,dstSubFolder=self.getLocalPath(self.transferer['pathPattern']),delete_after=False)
				if rtn is False:
					# No transfer due to outside restricted period. No status update
					return
			self.logger.info(
				"Transfer achieved in folder {0}"
				.format(self.getLocalPath(self.transferer['pathPattern']))
			)
			if self.transferer['delete_after']:
				try:
					self.downloader.delete_torrent(self['downloader_id'])
				except:
					self.logger.error("Unable to delete source file {0}. Ignoring".format(myFile))
		else:
			self.logger.debug("Transferer is disabled. No download")
		self.set(status=39)
		self.update(force=True)

	def pushTorrent(self,filename,downloader=None,delTorrent=True):
		if delTorrent is not True:
			self.logger.warning("delTorrent parameter is depreciate since it is now part of the configuration. Ignoring")
		if self['season'] * self['episode'] < 1:
			raise Exception("Season & episode are not set")
		if not isinstance(filename,basestring):
			raise Exception("Filename argument must be a basestring")
		self._setDownloader(downloader,True)

		now = datetime.datetime.now(tzlocal.get_localzone())
		downloader_id=unicode(self.downloader.add_torrent(filename))
		if int(downloader_id) > 0:
			self.set(status=30,downloader_id=downloader_id,nextUpdate=now)
			return
		else:
			raise Exception("Fail to add torrent")

	def getLocalPath(self,pathPattern=None):
		if pathPattern is None:
			pathPattern = "{seriesname}/season {seasonnumber}"

		if not self.isInfoUpdated():
			self.updateInfo(force=True)

		return pathPattern.format(
			seriesname=self['info']['seriesname'],
			seasonnumber=self['season'],
			episodenumber=self['episode'],
			)
