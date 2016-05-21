#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import os
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
from auth import AuthController, require, member_of, name_is
import utils.TSWdirectories

from cherrypy.process.plugins import Daemonizer
from cherrypy.process.plugins import PIDFile
from cherrypy.lib.static import serve_file

#cherrypy.server.ssl_module = 'builtin'
#cherrypy.server.ssl_certificate = "/home/boris/TvShowWatch-2/cert.pem"
#cherrypy.server.ssl_private_key = "/home/boris/TvShowWatch-2/privkey.pem"

curPath = os.path.dirname(os.path.realpath(__file__))
directories = utils.TSWdirectories(curPath+'/utils/directory.conf')
tmpPath = os.path.abspath(directories['tmp_path'])
PIDFile(cherrypy.engine, tmpPath + '/TSW2.PID').subscribe()
webPath = os.path.abspath(directories['web_path'])
confPath = os.path.abspath(directories['etc_path'])

class RestrictedArea:
    # all methods in this controller (and subcontrollers) is
    # open only to members of the admin group

    _cp_config = {
        'auth.require': [member_of('admin')]
    }
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"

    @cherrypy.expose
    def index(self):
        return """This is the admin only area."""

class Root(object):
	auth = AuthController()

	_cp_config = {
        'auth.require': []
    }

	@cherrypy.expose
	def index(self):
	    return serve_file(webPath+"index.html","text/html")

	@cherrypy.expose
	def default(self, page):
	    path = os.path.join(webPath, page)
	    return serve_file(path, content_type='text/html')

class LiveSearch(object):
	@cherrypy.expose
	@require()
	def index(self):
		return ""

	@cherrypy.expose
	@require()
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

class serv_TvShowList(object):
	def __init__(self,tvshowlist,downloader):
		self.tvshowlist = tvshowlist
		self.downloader=downloader
		self.checkModification()

	@cherrypy.expose
	@require()
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
	@require()
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
	@require()
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
				nextUpdate = datetime.datetime.now(tzlocal.get_localzone())
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
				return {"status":200,"error":"TvShow {0} updated".format(tvShow['info']['seriesname'])}
			else:
				return self._error(400,"{0} - {1}:{2}".format(e[0],fname,exc_tb.tb_lineno))
		else:
			return self._error(400,"Unknown TV Show")

	@cherrypy.expose
	@require()
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
						os.remove(tmpfile)
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
	@require()
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
	@require()
	@cherrypy.tools.json_out()
	def list(self):
		self.checkModification()
		return {"status":200,"error":"TvShow list retrieved in `data`","data":json.loads(json.dumps(self.tvshowlist.getValue(hidePassword=True),default=json_serial)),"debug":[]}

	def checkModification(self):
		"""if not hasattr(self,"lastModified") or os.path.getmtime(self.tvshowlist.filename) != self.lastModified:
			self.tvshowlist.addData(dataFile=curPath+"/series.json")
			self.lastModified = os.path.getmtime(self.tvshowlist.filename)"""

	@cherrypy.expose
	@require()
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

class updateData(object):
	def __init__(self,config):
		self.config = config

	@cherrypy.expose
	@require()
	@cherrypy.tools.json_out()
	def index(self,**params):
		try:
			self.config.updateData(json.loads(params['data'.encode('utf8')]))
			return {
				"status":200,
				"error":"Configuration updated!".encode("utf8"),
				"id":params['id'.encode('utf8')],
				"data":json.loads(params['data'.encode('utf8')])
			}
		except jsonschema.ValidationError as e:
			return {"status":400,"error":"Form validation failed. The main cause of this error can be one of keywords is empty".encode("utf8")}
		except Exception as e:
			raise Exception(unicode(list(e)))
			return {"status":400,"error":e[0].encode("utf8")}

class streamGetSeries(object):
	def __init__(self,tvshowlist,downloader):
		self.tvshowlist = tvshowlist
		self.downloader = downloader

	@cherrypy.expose
	@require()
	def index(self):
		cherrypy.response.headers["Content-Type"] = "text/event-stream"
		cherrypy.response.headers['Cache-Control'] = 'no-cache'
		cherrypy.response.headers['Connection'] = 'keep-alive'

		def content():
			yield "retry: 5000\r\n"
			while True:
				for tvshow in self.tvshowlist:
					data = 'id: progression\r\ndata: {\r\n'
					data += 'data: "' + unicode(tvshow.seriesid) + '":' + unicode(tvshow.get_progression(self.downloader)) + "\r\n"
					data += 'data: }\n\n'
					yield data
				data = "id: server-time\r\ndata: " + time.ctime(os.path.getmtime(confPath+"/series.json")) + "\n\n"
				yield data
				time.sleep(5)

		return content()
	index._cp_config = {'response.stream': True, 'tools.encode.encoding':'utf-8'}


#if __name__ == '__main__':
def main():
	conf = {
		"/".encode('utf8') : {
			'tools.staticdir.on': True,
			'tools.staticdir.root':webPath,
			'tools.staticdir.dir': '.',
			'tools.staticdir.index': 'index.html',
			'tools.trailing_slash.on' : False,
			'tools.sessions.on': True,
			'tools.auth.on': True,
            'tools.response_headers.headers':[
                { 'Access-Control-Allow-Credentials': True },
                { 'Access-Control-Allow-Origin':'localhost'}
            ]
			#'auth.require':[]
		},
		"/livesearch".encode('utf8') : {

		},
		"/tvshowlist".encode('utf8') : {

		},
		"/streamGetSeries".encode('utf8') : {
		},
		"/status.json".encode('utf8'): {
			"tools.staticfile.on": True,
			"tools.staticfile.filename": webPath + "/tvShowSchedule/status.json"
		},
        '/favicon.ico'.encode('utf8'):
        {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': webPath + '/static/favicon.ico',
        },
	}

	torrentsearch = torrentSearch.torrentSearch("torrentSearch",dataFile=confPath+"/config.json",verbosity=False)
	downloader = Downloader.Downloader("downloader",dataFile=confPath+"/config.json")
	transferer = Transferer.Transferer("transferer",dataFile=confPath+"/config.json")
	tvshowlist = tvShowList.tvShowList(id="tvShowList",tvShows=confPath+"/series.json",banner_dir=webPath+"/static",verbosity=False)
	notificator = Notificator.Notificator(id="notificator",dataFile=confPath+"/config.json",verbosity=False)
	root = Root()
	root.update = Root()
	root.livesearch = LiveSearch()
	root.tvshowlist = serv_TvShowList(tvshowlist=tvshowlist,downloader=downloader)
	root.streamGetSeries = streamGetSeries(tvshowlist=tvshowlist,downloader=downloader)

	cherrypy.config["tools.encode.on"] = True
	cherrypy.config["tools.encode.encoding"] = "utf-8"
	cherrypy.config['engine.autoreload_on'] = False
	cherrypy.config['server.socket_port'] = 1205
	cherrypy.config['server.socket_host'] = '0.0.0.0'.encode('utf8')

	root = torrentsearch.getRoot(root)
	conf = torrentsearch.getConf(conf)
	root.update.torrentSearch = updateData(torrentsearch)

	root = downloader.getRoot(root)
	conf = downloader.getConf(conf)
	root.update.downloader = updateData(downloader)

	root = transferer.getRoot(root)
	conf = transferer.getConf(conf)
	root.update.transferer = updateData(transferer)

	root = notificator.getRoot(root)
	conf = notificator.getConf(conf)
	root.update.notificator = updateData(notificator)

	def backgoundProcess(tvshowlist,downloader,transferer,searcher,force):
		tvshowlist.update(downloader=downloader,transferer=transferer,searcher=searcher,notificator=notificator,force=force)

	wd = cherrypy.process.plugins.BackgroundTask(
			interval=10,
			function=backgoundProcess,
			kwargs={
				"tvshowlist":tvshowlist,
				"downloader":downloader,
				"transferer":transferer,
				"searcher":torrentsearch,
				"force":False
			}
	)
	wd.start()

	cherrypy.quickstart(root,"/".encode('utf8'),conf)

# By jgbarah from http://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable-in-python
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type {0} not serializable".format(type(obj)))
