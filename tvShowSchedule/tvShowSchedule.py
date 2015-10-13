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

t = myTvDB.myTvDB()
	
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
	if not isinstance(tvShow,int):
		raise TypeError("Incorrect argument: {0}".format(unicode(tvShow).encode('utf8')))
	return tvShowScheduleFromMyTvDB(t[int(tvShow)])

class tvShowSchedule(object):
	def __init__(self, id, title, season=0, episode=0,status=0, nextUpdate=None):
		self.id = int(id)
		self.title = unicode(title)
		if isinstance(nextUpdate,datetime.datetime):
			self.nextUpdate = nextUpdate
		else:
			self.nextUpdate = datetime.datetime.now() + datetime.timedelta(minutes=2)
		self.season = int(season) if int(season)>0 else 1
		self.episode = int(episode) if int(episode)>0 else 1
		if int(status) not in STATUS.keys():
			raise Exception("Incorrect status: {0}".format(unicode(status).encode('utf8')))
		self.status = int(status)
		
	
		
			
	
