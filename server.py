#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import os
import pwd, grp
import hashlib
import shutil
import json
import jsonschema
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
import Notificator
import tvShowList
import myTvDB
import ActivityLog
import utils.TSWdirectories
import ConfTest
import Server

from cherrypy.process.plugins import Daemonizer
from cherrypy.process.plugins import PIDFile

curPath = os.path.dirname(os.path.realpath(__file__))
directories = utils.TSWdirectories(curPath+'/utils/directory.conf')
tmpPath = os.path.abspath(directories['tmp_path'])
PIDFile(cherrypy.engine, tmpPath + '/TSW2.PID').subscribe()

threadCollection=[]

def buffyThreadSlayer():
	for t in threadCollection:
		if not t.isAlive():
			t.join()

testPath = unicode(tempfile.mkdtemp())

def _stop():
	print("Removing {0}".format(testPath))
	shutil.rmtree(testPath)

cherrypy.engine.signal_handler.set_handler(signal=15,listener=_stop)
cherrypy.engine.signal_handler.subscribe()

class Root(object):
	pass

class serv_TvShowList(object):
	def __init__(self,tvshowlist,downloader,searcher):
		self.tvshowlist = tvshowlist
		self.downloader=downloader
		self.searcher=searcher
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
		return {"status":200,"error":"TvShow {0} added".format(tvShowName),"data":json.loads(json.dumps(tvShow.getValue(),default=Server.json_serial))}

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
	def forceUpdate(self):
		for tvShow in self.tvshowlist:
			self.update(tvShowID=tvShow['seriesid'],force=True)
		return {"status":200,"error":"All TvShows will be updated now"}

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
			emails=None
			keywords=None
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
				status = 0
			if 'pattern' in kwargs.keys():
				pattern = unicode(kwargs['pattern'])
			if 'emails[]' in kwargs.keys():
				if isinstance(kwargs['emails[]'],basestring):
					emails = [kwargs['emails[]']]
				else:
					emails = kwargs['emails[]']

			if 'keywords[]' in kwargs.keys():
				if isinstance(kwargs['keywords[]'],basestring):
					keywords = [kwargs['keywords[]']]
				else:
					keywords = kwargs['keywords[]']

			if any(item in ['season','episode','keywords[]','pattern','force'] for item in kwargs.keys()):
				nextUpdate = datetime.datetime.now(tzlocal.get_localzone())
			tvShow = self.tvshowlist.getTvShow(tvShowID)
			if tvShow is None:
				raise Exception("{0} not found in {1}".format(tvShowID,list(self.tvshowlist)))
			fname = ""
			self.tvshowlist.lock.acquire()
			try:
				self.checkModification()
				tvShow.set(
					status=status,
					season=season,
					episode=episode,
					nextUpdate=nextUpdate,
					pattern=pattern,
					emails=emails,
					keywords=keywords
				)
				self.tvshowlist.save()
			except Exception as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			finally:
				self.tvshowlist.lock.release()
			if fname == "":
				return {
					"status":200,
					"error":"TvShow {0} updated".format(
						tvShow['info']['seriesname']
					),
					"data":json.loads(
						json.dumps(
							tvShow.getValue(),
							default=Server.json_serial
						)
					)
				}
			else:
				return self._error(400,"{0} - {1}:{2}".format(e[0],fname,exc_tb.tb_lineno))
		else:
			return self._error(400,"Unknown TV Show")

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def pushTorrent(self, **kwargs):
		if 'tvShowID' in kwargs.keys() and self.tvshowlist.inList(int(kwargs['tvShowID'])):
			tvShowID = int(kwargs['tvShowID'])
			if 'torrentFile' in kwargs.keys():
				if not isinstance(kwargs['torrentFile'],basestring):
					tvShow = self.tvshowlist.getTvShow(int(tvShowID))
					try:
						tmpfile = tempfile.gettempdir() + '/out.torrent'
						with open(tmpfile, 'wb') as f:
							f.write(kwargs['torrentFile'].file.read())
						tvShow.pushTorrent(filename=tmpfile,downloader=self.downloader)
						return {"status":200,"error":"TvShow {0} updated".format(tvShow['info']['seriesname'])}
					except Exception as e:
						return self._error(400,e[0])
				else:
					return self._error(400,"Unable to upload file")
			else:
				return self._error(400,"No file provided")
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
		return {"status":200,"error":"TvShow list retrieved in `data`","data":json.loads(json.dumps(self.tvshowlist.getValue(hidePassword=True),default=Server.json_serial)),"debug":[]}

	def checkModification(self):
		"""if not hasattr(self,"lastModified") or os.path.getmtime(self.tvshowlist.filename) != self.lastModified:
			self.tvshowlist.addData(dataFile=curPath+"/series.json")
			self.lastModified = os.path.getmtime(self.tvshowlist.filename)"""

	@cherrypy.expose
	def progression(self,tvShowID=-1):
		tvShowID = int(tvShowID)
		tvShow = self.tvshowlist.getTvShow(tvShowID)
		if tvShow is None:
			cherrypy.response.headers["Content-Type"] = "application/json"
			return self._error(400,"Unknown TV Show")

		cherrypy.response.headers["Content-Type"] = "text/event-stream"
		cherrypy.response.headers['Cache-Control'] = 'no-cache'
		cherrypy.response.headers['Connection'] = 'keep-alive'
		def content():
			yield "retry: 5000\r\n"
			while True:
				data = "Event: progression\r\ndata: " + json.dumps(tvShow.get_progression(self.downloader)) + "\n\n"
				yield data
				time.sleep(5)

		return content()
	progression._cp_config = {'response.stream': True, 'tools.encode.encoding':'utf-8'}

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def setDefaultKeywords(self,tvShowID=-1):
		params = {'tvShowID':tvShowID}
		keywords = self.searcher.data.setdefault('defaultKeywords',[])
		params['keywords[]'] = keywords
		return self.update(**params)

class updateData(object):
	def __init__(self,config,testPath=None):
		self.config = config
		self.testPath = testPath
		if testPath is not None:
			className = self.config.__module__.split(".")[:-1]
			self.className = '.'.join(className)
			self.dataFile = os.path.join(testPath,"test.json")

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self,**params):
		try:
			self.config.updateData(json.loads(params['data'.encode('utf8')]))
			if self.testPath is not None:
				buffyThreadSlayer()
				c=ConfTest.ConfTest(dataFile=self.dataFile,confFile=self.config.dataFile,resultPath=self.testPath,verbosity=True)
				c.addTest('.'.join([self.className,'ConfTest']))
				t = threading.Thread(target=c.runAll)
				t.daemon=True
				threadCollection.append(t)
				t.start()
			return {
				"status":200,
				"error":"Configuration updated!".encode("utf8"),
				"id":params['id'.encode('utf8')],
				"data":json.loads(params['data'.encode('utf8')])
			}
		except jsonschema.ValidationError as e:
			return {"status":400,"error":"Form validation failed. The main cause of this error can be one of keywords is empty".encode("utf8")}
		except Exception as e:
			return {"status":400,"error":e[0].encode("utf8")}

	@cherrypy.expose
	@cherrypy.tools.json_out()
	def confTest(self,**params):
		if self.testPath is not None:
			c=ConfTest.ConfTest(dataFile=self.dataFile,confFile=self.config.dataFile,resultPath=self.testPath,verbosity=True)
			index = c.getTestIndex('.'.join([self.className,'ConfTest']))
			if index is not None:
				data = c['suite'][index]
				filename = os.path.join(self.testPath,self.className)
				if os.path.isfile(filename):
					with open(filename,'r') as fd:
						content = fd.read()
					data["content"] = content
				return json.loads(json.dumps(data,default=Server.json_serial))

class streamGetSeries(object):
	def __init__(self,tvshowlist,downloader,testPath=None,testFiles=None):
		self.tvshowlist = tvshowlist
		self.downloader = downloader
		self.testPath = testPath
		self.testFiles = [] if testFiles is None else testFiles
		self.testFilesMd5 = dict()

	@cherrypy.expose
	def index(self):
		cherrypy.response.headers["Content-Type"] = "text/event-stream"
		cherrypy.response.headers['Cache-Control'] = 'no-cache'
		cherrypy.response.headers['Connection'] = 'keep-alive'

		def content():
			yield "retry: 10000\r\n"
			while True:
				for tvshow in self.tvshowlist:
					data = 'id: progression\r\ndata: {\r\n'
					data += 'data: "' + unicode(tvshow.seriesid) + '":' + unicode(tvshow.get_progression(self.downloader)) + "\r\n"
					data += 'data: }\n\n'
					yield data
				#data = "id: server-time\r\ndata: " + time.ctime(os.path.getmtime(confPath+"/series.json")) + "\n\n"
				data = "id: server-time\r\ndata: " + Server.md5sum(confPath+"/series.json") + "\n\n"
				if self.testPath is not None:
					for testFile in self.testFiles:
						filename = os.path.join(self.testPath,testFile)
						if os.path.isfile(filename):
							if (testFile not in self.testFilesMd5.keys()
								or self.testFilesMd5[testFile] != Server.md5sum(filename)):
								data = "id: conf-test\r\ndata: " + testFile + "\n\n"
								self.testFilesMd5[testFile] = Server.md5sum(filename)
				yield data
				time.sleep(10)

		return content()
	index._cp_config = {'response.stream': True, 'tools.encode.encoding':'utf-8'}

webPath = os.path.abspath(directories['web_path'])
confPath = os.path.abspath(directories['etc_path'])

#if __name__ == '__main__':
def main():
	conf = {
		"/".encode('utf8') : {
			'tools.staticdir.on': True,
			'tools.staticdir.root':webPath,
			'tools.staticdir.dir': '.',
			'tools.staticdir.index': 'index.html',
			'tools.trailing_slash.on' : False,
			'tools.caching.on' : False
		},
		"/status.json".encode('utf8'): {
			"tools.staticfile.on": True,
			"tools.staticfile.filename": webPath + "/tvShowSchedule/status.json"
		},
		'/favicon.ico'.encode('utf8'):
		{
			'tools.staticfile.on': True,
			'tools.staticfile.filename': webPath + '/static/favicon.ico'
		}
	}

	torrentsearch = torrentSearch.torrentSearch("torrentSearch",dataFile=confPath+"/config.json",verbosity=False)
	downloader = Downloader.Downloader("downloader",dataFile=confPath+"/config.json")
	transferer = Transferer.Transferer("transferer",dataFile=confPath+"/config.json")
	tvshowlist = tvShowList.tvShowList(id="tvShowList",tvShows=confPath+"/series.json",banner_dir=webPath+"/static",verbosity=False)
	notificator = Notificator.Notificator(id="notificator",dataFile=confPath+"/config.json",verbosity=False)
	activitylog = ActivityLog.ActivityLog(confPath+"/activityLog.db",verbosity=False)
	root = Root()
	root.update = Root()
	root.livesearch = Server.LiveSearch()
	root.tvshowlist = serv_TvShowList(tvshowlist=tvshowlist,downloader=downloader,searcher=torrentsearch)
	root.activitylog = Server.ActivityLog(activitylog)

	root.streamGetSeries = streamGetSeries(
		tvshowlist=tvshowlist,
		downloader=downloader,
		testPath  =testPath,
		testFiles =['torrentSearch','Downloader']
	)
	root.users = Server.Users()
	root.groups = Server.Groups()

	cherrypy.config["tools.encode.on"] = True
	cherrypy.config["tools.encode.encoding"] = "utf-8"
	cherrypy.config['engine.autoreload_on'] = False
	cherrypy.config['server.socket_port'] = 1205
	cherrypy.config['server.socket_host'] = '0.0.0.0'.encode('utf8')

	root = torrentsearch.getRoot(root)
	conf = torrentsearch.getConf(conf)
	root.update.torrentSearch = updateData(torrentsearch,testPath)

	root = downloader.getRoot(root)
	conf = downloader.getConf(conf)
	root.update.downloader = updateData(downloader,testPath)

	root = transferer.getRoot(root)
	conf = transferer.getConf(conf)
	root.update.transferer = updateData(transferer)

	root = notificator.getRoot(root)
	conf = notificator.getConf(conf)
	root.update.notificator = updateData(notificator)

	wd = cherrypy.process.plugins.BackgroundTask(
			interval=10,
			function=Server.backgoundProcess,
			kwargs={
				"tvshowlist":tvshowlist,
				"downloader":downloader,
				"transferer":transferer,
				"searcher":torrentsearch,
				"notificator":notificator,
				"activitylog":activitylog,
				"force":False
			}
	)
	wd.start()

	wd = cherrypy.process.plugins.BackgroundTask(
		interval=1,
		function=buffyThreadSlayer
	)

	cherrypy.quickstart(root,"/".encode('utf8'),conf)
