#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import datetime
import json
import JSAG
import myTvDB

path = os.path.dirname(os.path.realpath(__file__))
with open(path + '/status.json') as data_file:    
	STATUS = json.load(data_file)
for key,item in STATUS.items():
	STATUS[int(key)] = item
	
def resetTvDB():
	global t
	t = myTvDB.myTvDB()
	
resetTvDB()
	
def tvShowScheduleFromMyTvDB(tvShow):
	if not isinstance(tvShow,myTvDB.myShow):
		raise TypeError("Incorrect argument: {0} ({1})".format(unicode(tvShow).encode('utf8'),type(tvShow)))
	next = tvShow.nextAired()
	if next is None:
		season = 0
		episode = 0
		status = 90
		nextUpdate = datetime.datetime.now() + datetime.timedelta(days=7)
	else:
		season = int(next['seasonnumber'])
		episode = int(next['episodenumber'])
		status = 10
		nextUpdate = datetime.strptime(next['firstaired'],'%Y-%m-%d')
	return tvShowSchedule(id=tvShow['id'],title=tvShow['seriesname'],season=season,episode=episode,status=status,nextUpdate=nextUpdate)
	
def tvShowScheduleFromId(tvShow):
	global t
	if not isinstance(tvShow,int):
		raise TypeError("Incorrect argument: {0}".format(unicode(tvShow).encode('utf8')))
	return tvShowScheduleFromMyTvDB(t[int(tvShow)])
	
def fakeTvDB(tvDB):
	global t
	if not isinstance(tvDB,myTvDB.myTvDB):
		raise TypeError("Incorrect argument: {0}".format(unicode(tvDB).encode('utf8')))
	t=tvDB

class tvShowSchedule(object):
	def __init__(self, id, title, season=0, episode=0,status=0, nextUpdate=None):
		self.id = int(id)
		self._set(title=unicode(title), season=season, episode=episode,status=status, nextUpdate=nextUpdate)
		
	def _set(self,title=None,season=None,episode=None,status=None,nextUpdate=None):
		if title is not None:
			self.title = unicode(title)
		if season is not None:
			self.season = int(season) if int(season)>0 else 0
		if episode is not None:
			self.episode = int(episode) if int(episode)>0 else 0
		if status is not None:
			if int(status) not in STATUS.keys():
				raise Exception("Incorrect status: {0}".format(unicode(status).encode('utf8')))
			self.status = int(status)
		if isinstance(nextUpdate,datetime.datetime):
			self.nextUpdate = nextUpdate
		else:
			self.nextUpdate = datetime.datetime.now() + datetime.timedelta(minutes=2)
			
	def _setAchieved(self):
		nextUpdate = datetime.datetime.now() + datetime.timedelta(days=7)
		self._set(season = 0,episode = 0,status = 90,nextUpdate=nextUpdate)
		
	def _setNotYetAired(self,episode):
		nextUpdate = min(datetime.datetime.strptime(episode['firstaired'],'%Y-%m-%d'),datetime.datetime.now()+datetime.timedelta(days=7))
		self._set(season=int(episode['seasonnumber']),episode=int(episode['episodenumber']),status=10,nextUpdate=nextUpdate)
		
	def update(self,force=False):
		global t
		if force or self.nextUpdate < datetime.datetime.now():
			# Added
			if self.status == 0:
				if self.season * self.episode > 0:
					firstaired = datetime.datetime.strptime(t[self.id][self.season][self.episode]['firstaired'],'%Y-%m-%d')
					if firstaired < datetime.datetime.now():
						self._set(status=20)
						self.update(force=True)
					else:
						self._setNotYetAired(t[self.id][self.season][self.episode])
				else:
					tvShow = t[self.id]
					next = tvShow.nextAired()
					if next is None:
						self._setAchieved()
					else:
						self._setNotYetAired(next)
			# Not yet aired
			elif self.status == 10:
				firstaired = datetime.datetime.strptime(t[self.id][self.season][self.episode]['firstaired'],'%Y-%m-%d')
				if firstaired < datetime.datime.now():
					self._set(status=20)
					self.update(force=True)
				else:
					self._setNotYetAired(t[self.id][self.season][self.episode])
			
			# Torrent watch
			elif self.status == 20:
				#TODO Search Torrent 
				nextUpdate = datetime.datetime.now()+datetime.timedelta(minutes=15)
				self._set(nextUpdate=nextUpdate)
			
			# Download in progress
			elif self.status == 30:
				#TODO Check Download
				nextUpdate = datetime.datetime.now()+datetime.timedelta(minutes=15)
				self._set(nextUpdate=nextUpdate)
				
			# Broadcast achieved
			elif self.status == 90:
				tvShow = t[self.id]
				next = tvShow.nextAired()
				if next is None:
					self._setAchieved()
				else:
					self._setNotYetAired(next)
	
