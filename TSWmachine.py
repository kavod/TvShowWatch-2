#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import json
import datetime
import threading
import Downloader
import torrentSearch
import Transferer
import tvShowList
import myTvDB
import logging

#class MyThread(threading.Thread):
def run():
	logging.error('run!')
	curPath = os.path.dirname(os.path.realpath(__file__))
	torrentsearch = torrentSearch.torrentSearch("torrentSearch",dataFile=curPath+"/config.json")
	downloader = Downloader.Downloader("downloader",dataFile=curPath+"/config.json")
	transferer = Transferer.Transferer("transferer",dataFile=curPath+"/config.json")
	#while not self.stopped.wait(60):
	tvshowlist = tvShowList.tvShowList(id="tvShowList",tvShows=curPath+"/series.json",verbosity=False)
	tvshowlist.update(downloader=downloader,transferer=transferer,searcher=torrentsearch,force=False)
	tvshowlist.save()
