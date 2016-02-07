#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import transmissionrpc
import logging
import JSAG

class Downloader(object):
	def __init__(self,verbosity=False):
		logger = logging.getLogger()
		if verbosity:
			logger.setLevel(logging.DEBUG)
		logging.debug("[Downloader] Verbosity is set to {0}".format(unicode(verbosity)))
		self.confSchema = JSAG.loadParserFromFile("Downloader/downloader.jschem")
		self.conf = JSAG.JSAGdata(configParser=self.confSchema,value={})
		self.transmission = None
		
	def loadConfig(self,confFile,path=[]):
		self.conf.setFilename(confFile,path=path)
		try:
			logging.info('[Downloader] config file {0} will be loaded.'.format(confFile))
			self.conf.load()
		except IOError:
			logging.info( "File does not exist. Creating a new one")
			self.conf.save()

	def cliConf(self):
		self.conf.cliCreate()
		self.conf.proposeSave(display=True)
		
	def displayConf(self):
		self.conf.display()
		
	def add_torrent(self,tor,delTorrent=True):
		logging.info('[Downloader] Add_torrent method called, client is {0}'.format(self.conf.getValue(['client'])))
		if self.conf.getValue(['client']) == 'transmission':
			if not self._transAvailableSlot():
				self._transClean()
			result = self.transmission.add_torrent('file://{0}'.format(tor))
			if isinstance(result,transmissionrpc.Torrent):
				if delTorrent:
					os.remove(tor)
				return unicode(result.id)
				
	def get_status(self,id):
		if self.conf.getValue(['client']) == 'transmission':
			if ( isinstance(id,unicode) or isinstance(id,str) ) and id.isdigit():
				id = int(id)
			if isinstance(id,int):
				return self.transmission.get_torrent(id).status
			else:
				raise Exception("Incorrect identifier: {0}".format(id))
		
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
			return len(tor)+1 <= self.transConf['maxSlots']
		else:
			return True

	def _transClean(self):
		logging.info('[Downloader] Max slots reached, removing 1 achieved torrent with {0} method'.format(self.transConf['cleanMethod']))
		torrents = self.transmission.get_torrents()
		torrents = [ tor for tor in torrents if tor.status == 'seeding']
		if self.transConf['cleanMethod'] == 'oldest':
			torrents = sorted(torrents, key=lambda tor: tor.date_added)
		elif self.transConf['cleanMethod'] == 'sharest':
			torrents = sorted(torrents, key=lambda tor: tor.uploadRatio,reverse=True)
		else:
			raise Exception("Unknown clean method: {0}".format(unicode(self.transConf['cleanMethod'])))
		logging.info('[Downloader] {0} torrent eligible for cleaning: {1}'.format(len(torrents),torrents))
		if len(torrents)<1:
			raise Exception("No eligible torrent for cleaning")
		id = torrents[0].id
		logging.info('[Downloader] Removing {0}'.format(torrents[0]))
		return self.transmission.remove_torrent(id, delete_data=True)['id']
