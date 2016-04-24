#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import json
import cherrypy
from cherrypy.lib import auth_digest
import threading
import datetime
import tzlocal
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
		self.checkModification()

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self):
		return {"status":400,"error":""}
		
	def _error(self,errorNo,errorDesc):
		return {"status":errorNo,"error":errorDesc.encode("utf8")}
		
	def _add(self,tvShowID,tvShowName):
		self.checkModification()
		try:
			self.tvshowlist.add(int(tvShowID))
			self.tvshowlist.save()
			tvShow = self.tvshowlist.getTvShow(int(tvShowID))
		except Exception as e:
			return self._error(400,e[0])
		return {"status":200,"error":"TvShow {0} added".format(tvShowName),"data":json.loads(json.dumps(tvShow.getValue(),default=json_serial))}
	
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def add(self, **kwargs):
		self.checkModification()
		if 'title' in kwargs.keys():
			seriesname = kwargs['title']
			if 'seriesid' in kwargs.keys():
				serie = int(kwargs['seriesid'])
			else:
				serie = seriesname
		else:
			serie = unicode(kwargs)
			seriesname = serie
		t = myTvDB.myTvDB()
		try:
			tvShow = t[serie]
		except Exception as e:
			return self._error(400,e[0]+unicode(serie)+unicode(seriesname.lower()))
		if tvShow.data['seriesname'].lower() == seriesname.lower():
			#cherrypy.request.params['tvShowID'] = tvShow.data['id']
			return self._add(tvShow.data['id'],tvShow.data['seriesname'])
		return {"status":401,"error":"Unknown TvShow: '{0}'".format(seriesname)}
		
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def update(self, **kwargs):
		if 'tvShowID' in kwargs.keys():
			tvShowID = int(kwargs['tvShowID'])
			nextUpdate=None
			status = None
			season = None
			episode=None
			pattern=None
			if 'season' in kwargs.keys() and 'episode' in kwargs.keys():
				season = int(kwargs['season'])
				episode = int(kwargs['episode'])
				t = myTvDB.myTvDB()
				try:
					t[tvShowID]
				except:
					return {"status":400,"error":"TvShow {0} does not exist".format(unicode(tvShowID))}
				try:
					t[tvShowID][season][episode]
				except:
					return {"status":400,"error":"No episode S{1:02}E{2:02} for TV show {0}".format(t[tvShowID].data['seriesname'],unicode(season),unicode(episode))}
				nextUpdate = datetime.datetime.now(tzlocal.get_localzone())
				status = 0
			if 'pattern' in kwargs.keys():
				pattern = unicode(kwargs['pattern'])
			self.checkModification()
			tvShow = self.tvshowlist.getTvShow(tvShowID)
			tvShow._set(status=status,season=season,episode=episode,nextUpdate=nextUpdate,pattern=pattern)
			self.tvshowlist.save()
			return {"status":200,"error":"TvShow {0} updated".format(tvShow['title'])}
		else:
			return self._error(400,"Unknown TV Show")
			
		
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def delete(self,tvShowID=-1):
		self.checkModification()
		try:
			tvShowID = int(tvShowID)
			t = myTvDB.myTvDB()
			tvShow = t[tvShowID]
			self.tvshowlist.delete(tvShowID)
			self.tvshowlist.save()
			return {"status":200,"error":"TvShow {0} deleted".format(tvShow['seriesname'])}
		except Exception as e:
			return self._error(400,e[0])
			
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def list(self):
		self.checkModification()
		return {"status":200,"error":"TvShow list retrieved in `data`","data":json.loads(json.dumps(self.tvshowlist.getValue(hidePassword=True),default=json_serial))}
		
	def checkModification(self):
		if not hasattr(self,"lastModified") or os.path.getmtime(self.tvshowlist.filename) != self.lastModified:
			self.tvshowlist = tvShowList.tvShowList(id="tvShowList",tvShows=curPath+"/series.json",banner_dir="web/static")
			self.lastModified = os.path.getmtime(self.tvshowlist.filename)

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
			'tools.staticdir.dir': './web',
			'tools.staticdir.index': 'index.html',
			'tools.trailing_slash.on' : False
		},
		"/web".encode('utf8') : {
			'tools.staticdir.on': True,
			'tools.staticdir.root':local_dir,
			'tools.staticdir.dir': './web',
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
		}
	}

	torrentsearch = torrentSearch.torrentSearch("torrentSearch",dataFile=curPath+"/config.json")
	downloader = Downloader.Downloader("downloader",dataFile=curPath+"/config.json")
	transferer = Transferer.Transferer("transferer",dataFile=curPath+"/config.json")
	tvshowlist = tvShowList.tvShowList(id="tvShowList",tvShows=curPath+"/series.json",banner_dir="web/static")
	
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
	
	#root = tvshowlist.getRoot(root)
	#conf = tvshowlist.getConf(conf)
	#root.update.tvshowlist = updateData(tvshowlist)
	
	wd = cherrypy.process.plugins.BackgroundTask(1, daemon.daemon)
	wd.start()
	
	cherrypy.quickstart(root,"/".encode('utf8'),conf)

# By jgbarah from http://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable-in-python
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type {0} not serializable".format(type(obj)))
