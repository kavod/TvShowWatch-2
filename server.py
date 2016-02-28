#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import json
import cherrypy
from cherrypy.lib import auth_digest
import JSAG3


class Root(object):
	pass

class updateData(object):
	def __init__(self,config):
		self.config = config
		
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self,**params):
		self.config.updateData(json.loads(params['data'.encode('utf8')]))
		return {"id":params['id'.encode('utf8')],"data":json.loads(params['data'.encode('utf8')])}

if __name__ == '__main__':
	curPath = os.path.dirname(os.path.realpath(__file__))
	local_dir = os.path.abspath(os.getcwd())
	conf = {
		"/".encode('utf8') : {
			'tools.staticdir.on': True,
			'tools.staticdir.root':local_dir,
			'tools.staticdir.dir': './',
			'tools.staticdir.index': 'index.html',
		}
	}
	root = Root()
	root.update = Root()
	cherrypy.config["tools.encode.on"] = True
	cherrypy.config["tools.encode.encoding"] = "utf-8"

	torrentSearch = JSAG3.JSAG3("torrentSearch",schemaFile=curPath+"/torrentSearch/torrentSearch.jschem",optionsFile=curPath+"/torrentSearch/torrentSearch.jopt",dataFile=curPath+"/config.json")
	root = torrentSearch.getRoot(root)
	conf = torrentSearch.getConf(conf)
	root.update.torrentSearch = updateData(torrentSearch)
	
	downloader = JSAG3.JSAG3("downloader",schemaFile=curPath+"/Downloader/downloader.jschem",optionsFile=curPath+"/Downloader/downloader.jopt",dataFile=curPath+"/config.json")
	root = downloader.getRoot(root)
	conf = downloader.getConf(conf)
	root.update.downloader = updateData(downloader)
	
	cherrypy.quickstart(root,"/".encode('utf8'),conf)

