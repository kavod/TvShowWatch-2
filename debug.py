#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import sys
import os
import json
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
import utils.TSWdirectories

curPath = os.path.dirname(os.path.realpath(__file__))
directories = utils.TSWdirectories(curPath+'/utils/directory.conf')
webPath = os.path.abspath(directories['web_path'])
confPath = os.path.abspath(directories['etc_path'])

torrentsearch = torrentSearch.torrentSearch("torrentSearch",dataFile=confPath+"/config.json")
downloader = Downloader.Downloader("downloader",dataFile=confPath+"/config.json")
transferer = Transferer.Transferer("transferer",dataFile=confPath+"/config.json")
tvshowlist = tvShowList.tvShowList(id="tvShowList",tvShows=confPath+"/series.json",banner_dir=webPath+"/static",verbosity=True)
notificator = Notificator.Notificator(id="notificator",dataFile=confPath+"/config.json",verbosity=False)

tvshowlist.update(downloader=downloader,transferer=transferer,searcher=torrentsearch,notificator=notificator,force=True,wait=True)
