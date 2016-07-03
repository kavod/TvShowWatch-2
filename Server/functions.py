#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import hashlib
import datetime

def md5sum(fname):
	hash_md5 = hashlib.md5()
	with open(fname, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()

def backgoundProcess(tvshowlist,downloader,transferer,searcher,notificator,activitylog,force):
    tvshowlist.update(
        downloader=downloader,
        transferer=transferer,
        searcher=searcher,
        notificator=notificator,
        activitylog=activitylog,
        force=force
    )

# By jgbarah from http://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable-in-python
def json_serial(obj):
	"""JSON serializer for objects not serializable by default json code"""
	if isinstance(obj, datetime.datetime):
		serial = obj.isoformat()
		return serial
	raise TypeError ("Type {0} not serializable".format(type(obj)))
