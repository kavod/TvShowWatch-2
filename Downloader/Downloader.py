#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import transmissionrpc
import JSAG

class Downloader(object):
	def __init__(self):
		self.confSchema = JSAG.loadParserFromFile("Downloader/downloader.jschem")
		self.conf = JSAG.JSAGdata(configParser=self.confSchema,value={})
		self.transmission = None
		
	def loadConfig(self,confFile,path=[]):
		self.conf.setFilename(confFile,path=path)
		try:
			self.conf.load()
		except IOError:
			print "File does not exist. Creating a new one"
			self.conf.save()

	def cliConf(self):
		self.conf.cliCreate()
		self.conf.proposeSave(display=True)
		
	def displayConf(self):
		self.conf.display()
		
	def add_torrent(self,tor):
		if self.conf.getValue(['client']) == 'transmission':
			if not self._transAvailableSlot():
				self._transClean()
		
	#TransmissionRPC
	def _transConnect(self):
		if self.transmission is None:
			self.transConf = self.conf['transConf'].getValue(hidePasswords=False)
			try:
				self.transmission = transmissionrpc.Client(
										address=self.transConf['address'], 
										port=self.transConf['port'], 
										user=self.transConf['username'], 
										password=self.transConf['password']
										)
			except:
				conf = self.conf['transConf'].getValue(hidePasswords=True)
				raise Exception("Transmission connection error {0}".format(unicode(conf)))
				
	def _transAvailableSlot(self):
		if self.conf.getValue(['client']) == 'transmission':
			if self.transmission is None:
				self._transConnect()
			tor = self.transmission.get_torrents()
			return len(tor)+1 < self.transConf['maxSlots']
		else:
			return True

	def _transClean(self):
		torrents = self.transmission.get_torrents()
		torrents = [ tor for tor in torrents if tor.status == 'seeding']
		if self.transConf['cleanMethod'] == 'oldest':
			torrent = sorted(torrents, key=lambda tor: tor.date_added)[0]
		elif self.transConf['cleanMethod'] == 'sharest':
			torrent = sorted(torrents, key=lambda tor: tor.uploadRatio,reverse=True)[0]
		else:
			raise Exception("Unknown clean method: {0}".format(unicode(self.transConf['cleanMethod'])))
		print "torrent {0} will be removed".format(unicode(torrent))
