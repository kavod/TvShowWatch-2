#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import torrentSearch
import JSAG
import JSAG.Prompt as Prompt

ts = torrentSearch.torrentSearch()
ts.loadConfig("torrentSearch/torrentSearch.json")

ts.displayConf()
choix = ['Configuration','Search']
reponse = Prompt.promptChoice("Possible actions",choix=choix,mandatory=False,cleanScreen=False)

if reponse == 0:
	ts.cliConf()
elif reponse == 1:
	reponse = Prompt.promptText("Search pattern",default = None,selected=[],warning='',password=False,mandatory=True,cleanScreen=True)
	tor = ts.search(reponse)
	if tor is not None:
		ts.download(tor)
