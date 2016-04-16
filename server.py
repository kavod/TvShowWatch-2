#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import json
import cherrypy
from cherrypy.lib import auth_digest
import threading
import tempfile
import time
import JSAG3
import Downloader
import torrentSearch
import Transferer
import tvShowList
import myTvDB
import daemon

from cherrypy.process.plugins import Daemonizer
from cherrypy.process.plugins import PIDFile

"""d = Daemonizer(cherrypy.engine)
d.subscribe()"""
PIDFile(cherrypy.engine, tempfile.gettempdir() + '/TSW2.PID').subscribe()

class Root(object):
	pass
	
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
			cherrypy.request.params['result'] = json.dumps(t.livesearch(vpath.pop()))
			return self.result
		else:
			return self.index
			
class serv_TvShowList(object):
	def __init__(self,tvshowlist):
		self.tvshowlist = tvshowlist

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self):
		return {"status":400,"error":""}
		
	def _error(self,errorNo,errorDesc):
		return {"status":errorNo,"error":errorDesc.encode("utf8")}
		
	def _add(self,tvShowID,tvShowName):
		try:
			self.tvshowlist.add(int(tvShowID))
			self.tvshowlist.save()
		except Exception as e:
			return self._error(400,e[0])
		return {"status":200,"error":"TvShow {0} added".format(tvShowName)}
	
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def add(self,search=""):
		seriesname = search
		t = myTvDB.myTvDB()
		try:
			tvShow = t[seriesname]
		except Exception as e:
			return self._error(400,e[0])
		if tvShow.data['seriesname'].lower() == seriesname.lower():
			cherrypy.request.params['tvShowID'] = tvShow.data['id']
			return self._add(tvShow.data['id'],tvShow.data['seriesname'])
		return {"status":401,"error":"Unknown TvShow: '{0}'".format(seriesname)}
		
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def delete(self,tvShowID=-1):
		#try:
		self.tvshowlist.delete(int(tvShowID))
		self.tvshowlist.save()
		return {"status":200,"error":"TvShow {0} deleted".format(tvShowID)}
		#except Exception as e:
		#	return self._error(400,e[0])

class updateData(object):
	def __init__(self,config):
		self.config = config
		
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self,**params):
		self.config.updateData(json.loads(params['data'.encode('utf8')]))
		return {"id":params['id'.encode('utf8')],"data":json.loads(params['data'.encode('utf8')])}
		
class streamGetSeries(object):
	@cherrypy.expose
	def index(self):
		cherrypy.response.headers["Content-Type"] = "text/event-stream"
		cherrypy.response.headers['Cache-Control'] = 'no-cache'
		cherrypy.response.headers['Connection'] = 'keep-alive'
		def content():
			yield "retry: 5000\r\n"
			while True:
				data = "Event: server-time\r\ndata: 4" + time.ctime(os.path.getmtime(curPath+"/series.json")) + "\n\n"
				yield data
				time.sleep(5)
				
		return content()
	index._cp_config = {'response.stream': True, 'tools.encode.encoding':'utf-8'} 

curPath = os.path.dirname(os.path.realpath(__file__))
local_dir = os.path.abspath(os.getcwd())

#if __name__ == '__main__':
def main():
	conf = {
		"/".encode('utf8') : {
			'tools.staticdir.on': True,
			'tools.staticdir.root':local_dir,
			'tools.staticdir.dir': './',
			'tools.staticdir.index': 'index.html',
			'tools.trailing_slash.on' : False
		},
		"/livesearch".encode('utf8') : {
			
		},
		"/tvshowlist".encode('utf8') : {
			
		},
		"/streamGetSeries".encode('utf8') : {
		},
		"/status.json".encode('utf8'): {
			"tools.staticfile.on": True,
			"tools.staticfile.filename": local_dir + "/tvShowSchedule/status.json"
		},
		"/static".encode('utf8'): {
			"tools.staticdir.on": True,
			"tools.staticdir.dir": "static"
		}
	}

	torrentsearch = torrentSearch.torrentSearch("torrentSearch",dataFile=curPath+"/config.json")
	
	downloader = Downloader.Downloader("downloader",dataFile=curPath+"/config.json")
	
	transferer = Transferer.Transferer("transferer",dataFile=curPath+"/config.json")
	
	tvshowlist = tvShowList.tvShowList(id="tvShowList",tvShows=curPath+"/series.json",banner_dir="static")
	
	root = Root()
	root.update = Root()
	root.livesearch = LiveSearch()
	root.tvshowlist = serv_TvShowList(tvshowlist=tvshowlist)
	root.streamGetSeries = streamGetSeries()
	
	cherrypy.config["tools.encode.on"] = True
	cherrypy.config["tools.encode.encoding"] = "utf-8"
	
	root = torrentsearch.getRoot(root)
	conf = torrentsearch.getConf(conf)
	root.update.torrentSearch = updateData(torrentsearch)
	
	root = downloader.getRoot(root)
	conf = downloader.getConf(conf)
	root.update.downloader = updateData(downloader)
	
	root = transferer.getRoot(root)
	conf = transferer.getConf(conf)
	root.update.transferer = updateData(transferer)
	
	root = tvshowlist.getRoot(root)
	conf = tvshowlist.getConf(conf)
	root.update.tvshowlist = updateData(tvshowlist)
	
	wd = cherrypy.process.plugins.BackgroundTask(1, daemon.daemon)
	wd.start()
	
	cherrypy.quickstart(root,"/".encode('utf8'),conf)

