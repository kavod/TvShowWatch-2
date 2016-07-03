#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import cherrypy
import myTvDB

class ActivityLog(object):
	def __init__(self,activitylog):
		self.activitylog = activitylog

	@cherrypy.expose
	def index(self):
		return ''

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def lastdownloads(self):
		t = myTvDB.myTvDB()
		last_downloads = self.activitylog.get_last_downloads()
		for dl in last_downloads:
			dl['seriesname'] = t[dl['seriesid']].data['seriesname']
		return last_downloads
