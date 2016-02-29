#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import tvShowSchedule
import datetime
import Downloader
import Transferer
import torrentSearch

tvShow = tvShowSchedule.tvShowSchedule(seriesid=73739,title='Lost',season=1,episode=1,status=0,nextUpdate=datetime.datetime.now(),verbosity=True)
downloader = Downloader.Downloader(id="downloader",dataFile="config.json")
transferer = Transferer.Transferer(id="transferer",dataFile="config.json")
torrentSearch = torrentSearch.torrentSearch(id="torrentSearch",dataFile="config.json")
tvShow.update(downloader=downloader,transferer=transferer,searcher=torrentSearch,force=True)
print(tvShow.getValue())
