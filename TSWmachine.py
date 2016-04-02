#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import json
import threading
import Downloader
import torrentSearch
import Transferer
import tvShowList
import myTvDB

class MyThread(threading.Thread):
	def __init__(self, event):
		threading.Thread.__init__(self)
		self.stopped = event

	def run(self):
		curPath = os.path.dirname(os.path.realpath(__file__))
		torrentsearch = torrentSearch.torrentSearch("torrentSearch",dataFile=curPath+"/config.json")
		downloader = Downloader.Downloader("downloader",dataFile=curPath+"/config.json")
		transferer = Transferer.Transferer("transferer",dataFile=curPath+"/config.json")
		while not self.stopped.wait(60):
			tvshowlist = tvShowList.tvShowList(id="tvShowList",tvShows=curPath+"/series.json",verbosity=True)
			tvshowlist.update(downloader=downloader,transferer=transferer,searcher=torrentsearch,force=False)
			tvshowlist.save()
