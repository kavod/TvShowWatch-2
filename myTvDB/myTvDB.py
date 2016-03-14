#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import os
import json
import argparse
import string
import logging
import requests
import re
import urllib
from datetime import datetime
import tvdb_api

class myTvDB(tvdb_api.Tvdb):
	def __init__(self,
                interactive = False,
                select_first = False,
                debug = False,
                cache = True,
                banners = False,
                actors = False,
                custom_ui = None,
                language = None,
                search_all_languages = True,
                apikey = 'A2894E6CB335E443',
                forceConnect=False,
                useZip=False,
                dvdorder=False):
		if debug:
			logging.basicConfig(level=logging.DEBUG)
			logging.debug("Debugger in set to On")
		tvdb_api.Tvdb.__init__(self,
                interactive = interactive,
                select_first = select_first,
                debug = False,
                cache = cache,
                banners = banners,
                actors = actors,
                custom_ui = custom_ui,
                language = language,
                search_all_languages = search_all_languages,
                apikey = apikey,
                forceConnect=forceConnect,
                useZip=useZip,
                dvdorder=dvdorder)

	def _setItem(self, sid, seas, ep, attrib, value):
		if sid not in self.shows:
			self.shows[sid] = myShow()
		return tvdb_api.Tvdb._setItem(self, sid, seas, ep, attrib, value)

	def _setShowData(self, sid, key, value):
		"""Sets self.shows[sid] to a new Show instance, or sets the data
		"""
		if sid not in self.shows:
			self.shows[sid] = myShow()
		return tvdb_api.Tvdb._setShowData(self, sid, key, value)
		
	def _setItem(self, sid, seas, ep, attrib, value):
		if sid not in self.shows:
			self.shows[sid] = myShow()
		if seas not in self.shows[sid]:
			self.shows[sid][seas] = tvdb_api.Season(show = self.shows[sid])
		if ep not in self.shows[sid][seas]:
			self.shows[sid][seas][ep] = myEpisode(season = self.shows[sid][seas])
		self.shows[sid][seas][ep][attrib] = value
		
	def livesearch(self, pattern):
		result = self._loadUrl('http://thetvdb.com/livesearch.php?q={0}'.format(urllib.quote(pattern.encode('utf8'), safe='')))
		result = re.sub('\s*([{,:])\s*(\w+)\s*([},:])\s*','\\1\"\\2\"\\3',result) # Add double quotes
		result = re.sub('\s*,\s*([},:\]])\s*','\\1',result) # remove extra comma
		return json.loads(result)['results']

class myShow(tvdb_api.Show):
	def lastAired(self):
		today = datetime.today()
		current = tvdb_api.Episode()
		current['firstaired'] = '1900-01-01'

		for key,season in self.items():
			if str(key)=="0":
				continue
			for episode in [episode for episode in season.values() if episode['firstaired'] is not None]:
				ep_firstaired = datetime.strptime(episode['firstaired'],'%Y-%m-%d')
				cur_firstaired = datetime.strptime(current['firstaired'],'%Y-%m-%d')
				if ep_firstaired==None:
					continue
				if ep_firstaired < today:
					if cur_firstaired < ep_firstaired:
						current = episode
		if current['firstaired'] == '1900-01-01':
			return None
		return current

	def nextAired(self):
		today = datetime.today()
		current = tvdb_api.Episode()
		current['firstaired'] = '2100-12-31'

		for key,season in self.items():
			if str(key)=="0":
				continue
			for episode in season.values():
				ep_firstaired = datetime.strptime(episode['firstaired'],'%Y-%m-%d')
				cur_firstaired = datetime.strptime(current['firstaired'],'%Y-%m-%d')
				if ep_firstaired==None:
					continue
				if ep_firstaired >= today:
					if cur_firstaired > ep_firstaired:
						current = episode
		if current['firstaired'] == '2100-12-31':
			return None
		return current

	def getEpisodes(self):
		result = [];
		for key,season in self.items():
			for episode in season.values():
				result.append(episode)
		return result

	def getSeasons(self):
		result = [];
		for key,season in self.items():
			result.append(str(key))
		return result
		
class myEpisode(tvdb_api.Episode):
	def next(self):
		epno = int(self.get(u'episodenumber', 0))
		logging.debug("{0} episodes in season, looking for episode {1}".format(len(self.season),(epno + 1)))
		if len(self.season) < (epno + 1):
			seasno = int(self.get(u'seasonnumber', 0))
			logging.debug("{0} seasons in TvShow, looking for S{1:02}E01".format(len(self.season.show),(seasno +1)))
			if len([season for season in self.season.show if season>0]) > (seasno +1):
				return self.season.show[seasno+1][1]
			else:
				return None
		else:
			return self.season[epno+1]

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"-a",
		"--action",
		default='',
		choices=['getSerie','getEpisodes','getEpisode'],
		help='action triggered by the script'
		)
	parser.add_argument(
		"-n",
		"--serieID",
		default='0',
		help='indicates the series ID'
		)
	args = parser.parse_args()
	if args.serieID.isdigit():
		serieID = int(args.serieID)
	else:
		args_split = args.serieID.split(',')
		if all(x.isdigit() for x in args_split) and len(args_split)>2:
			serieID = int(args_split[0])
			season = int(args_split[1])
			episode = int(args_split[2])
		else:
			serieID = 0
			season = 0
			episode = 0
	t = myTvDB()
	if args.action == 'getSerie':
		serie = t[serieID]
		print(json.dumps(serie.data))
	elif args.action == 'getEpisode':
		episode = t[serieID][season][episode]
		print(json.dumps(episode))
	elif args.action == 'getEpisodes':
		print(json.dumps(t[serieID].getEpisodes()))
	'''str_result = '{0} S{1:02}E{2:02}'
	last = t['how i met your mother'].lastAired()
	next = t['how i met your mother'].nextAired()
	print(str_result.format(last['episodename'],int(last['seasonnumber']),int(last['episodenumber'])))
	print(str_result.format(next['episodename'],int(next['seasonnumber']),int(next['episodenumber'])))'''

if __name__ == '__main__':
    main()
