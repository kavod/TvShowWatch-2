#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import json
import cherrypy
import myTvDB

class LiveSearch(object):
	@cherrypy.expose
	def index(self):
		return ""

	@cherrypy.expose
	def result(self,result):
		return result

	def _cp_dispatch(self,vpath):
		if len(vpath) == 1:
			t = myTvDB.myTvDB()
			try:
				cherrypy.request.params['result'] = json.dumps(t.livesearch(vpath.pop()))
			except:
				return self.index
			return self.result
		else:
			return self.index
