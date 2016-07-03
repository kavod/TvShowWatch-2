#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import tempfile
import cherrypy

def test_chownrestricted():
	tmpfile = unicode(tempfile.mkstemp('.txt')[1])
	try:
		os.chmod(tmpfile,0777)
		os.chown(tmpfile,0,0)
		result = True
	except OSError:
		result = False
	os.remove(tmpfile)
	return result

class Users(object):
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self):
		result = [{"value":-1,"text":"Default (process owner)"}]
		if test_chownrestricted():
			# Only if root or not _POSIX_CHOWN_RESTRICTED
			for p in pwd.getpwall():
				if (p[2] >= 1000 and p[2]<65534) or p[2]==0:
					result.append({"value":p[2],"text":p[0]})

		return result

class Groups(object):
	@cherrypy.expose
	@cherrypy.tools.json_out()
	def index(self):
		result = [{"value":-1,"text":"Default (process owner group)"}]
		if test_chownrestricted():
			# Only if root or not _POSIX_CHOWN_RESTRICTED
			for p in grp.getgrall():
				if (p[2] >= 1000 and p[2]<65534) or p[2]==0:
					result.append({"value":p[2],"text":p[0]})
		return result
