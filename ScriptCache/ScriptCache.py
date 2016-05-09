#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import re
import logging
import datetime
import tempfile
import urllib2
import shutil
import cherrypy

EXPIRY= datetime.timedelta(days=30)

class ScriptCache(object):
	def __init__(self,remoteURL,localFile,directory=".",expiry=EXPIRY,verbosity=None):
		if isinstance(directory,basestring):
			self.directory = directory
		else:
			raise TypeError("directory must be a basestring. Not {0}".format(type(directory)))
			
		if isinstance(localFile,basestring):
			p = re.compile('\w+')
			if p.match(localFile):
				self.localFile = unicode(localFile)
				self.loggerName = "ScriptCache.{0}".format(self.localFile)
			else:
				raise ValueError("Incorrect symbol in local filename '{0}'".format(unicode(localFile)))
		else:
			raise TypeError("localFile must be a basestring. Not {0}".format(type(localFile)))
			
		if isinstance(remoteURL,basestring):
			p = re.compile('^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?')
			m = p.match(remoteURL)
			if m:
				self.remoteURL = remoteURL
			else:
				raise ValueError("Remote URL not well formed")
		else:
			raise TypeError("remoteURL must be a string")
			
		self.logger = logging.getLogger(self.loggerName)
		if verbosity is not None and isinstance(verbosity,int):
			self.logger.setLevel(verbosity)
		self.logger.info("Creation of ScriptCache {0} from URL {1}".format(self.localFile,self.remoteURL))
		
		if isinstance(expiry,datetime.timedelta):
			self.expiry = expiry
		else:
			self.logger.warning(
				"expiry parameter must be datetime.timedelta instance. Got {0}. Defaulting to {1}".format(
					type(expiry),
					unicode(EXPIRY)
				)
			)
			self.expiry = EXPIRY
		
		if self._isUpdateNeeded():
			self._update()
		
	def _localFileAbsPath(self):
		return "{0}/{1}".format(self.directory,self.localFile)

	def _isUpdateNeeded(self):
		if os.path.isfile(self._localFileAbsPath()):
			lastModify = datetime.datetime.fromtimestamp(os.path.getmtime(self._localFileAbsPath()))
			if lastModify < datetime.datetime.now() - self.expiry:
				self.logger.info("'{0}' needs to be updated. Last modification: {1}".format(self.localFile,lastModify.isoformat()))
				return True
			else:
				return False
		else:
			self.logger.info("'{0}' not found in local.".format(self._localFileAbsPath()))
			return True
			
	def _update(self):
		tmpfile = unicode(tempfile.mkstemp()[1])
		try:
			try:
				response = urllib2.urlopen(self.remoteURL)
			except Exception as e:
				self.logger.error("Unable to retrive URL '{0}'".format(self.remoteURL))
			try:
				with open(tmpfile,'w') as fd:
					fd.write(response.read())
				shutil.move(tmpfile,self._localFileAbsPath())
				self.logger.info("URL {0} retrieved to {1}".format(self.remoteURL,self._localFileAbsPath()))
			except Exception as e:
				self.logger.error("Unable to write local file '{0}'.".format(self._localFileAbsPath()))
		finally:
			if os.path.isfile(tmpfile):
				os.remove(tmpfile)
	
	def _cp_dispatch(self,vpath):
		if len(vpath) == 1:
			pass
