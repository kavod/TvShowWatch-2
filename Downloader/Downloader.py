#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import transmissionrpc
import logging
import JSAG3

class Downloader(JSAG3.JSAG3):
	def __init__(self,id="downloader",dataFile=None,verbosity=False):
		curPath = os.path.dirname(os.path.realpath(__file__))
	
		JSAG3.JSAG3.__init__(self,
			id=id,
			schemaFile=curPath+"/downloader.jschem",
			optionsFile=curPath+"/downloader.jopt",
			dataFile=dataFile,
			verbosity=verbosity
		)
		self.transmission = None
		
	def loadConfig(self,confFile,path=[]):
		self.addData(confFile)
		
	def add_torrent(self,tor,delTorrent=True):
		logging.info('[Downloader] Add_torrent method called, client is {0}'.format(self.data['client']))
		if self.data['client'] == 'transmission':
			if not self._transAvailableSlot():
				self._transClean()
			try:
				result = self.transmission.add_torrent('file://{0}'.format(tor),paused=False)
			except transmissionrpc.TransmissionError as e:
				logging.error("[Downloader] Error when adding torrent: {0}".format(e.message))
				if delTorrent:
					os.remove(tor)
				return -1
			except Exception as e:
				logging.error("[Downloader] Error when adding torrent: {0}".format(e.args))
				if delTorrent:
					os.remove(tor)
				return -1
				
			if isinstance(result,transmissionrpc.Torrent):
				if delTorrent:
					os.remove(tor)
				return unicode(result.id)
				
	def get_status(self,id):
		logging.debug("[Downloader] client is {0}".format(unicode(self.data['client'])))
		if self.data['client'] == 'transmission':
			logging.debug("[Downloader] retrieving status of slot #{0}".format(unicode(id)))
			if ( isinstance(id,basestring) ) and id.isdigit():
				id = int(id)
			if isinstance(id,int):
				if self.transmission is None:
					self._transConnect()
				tor = self.transmission.get_torrent(id)
				logging.debug("[Downloader] torrent #{0}: {1}".format(unicode(id),unicode(tor)))
				status = tor.status
				logging.debug("[Downloader] Status of slot #{0} is {1}".format(unicode(id),status))
				return status
			else:
				logging.error("[Downloader] Incorrect identifier: {0}".format(unicode(id)))
				raise Exception("Incorrect identifier: {0}".format(id))
				
	def get_files(self,id):
		logging.debug("[Downloader] client is {0}".format(unicode(self.data['client'])))
		if self.data['client'] == 'transmission':
			logging.debug("[Downloader] retrieving files of slot #{0}".format(unicode(id)))
			if ( isinstance(id,basestring) ) and id.isdigit():
				id = int(id)
			if isinstance(id,int):
				if self.transmission is None:
					self._transConnect()
				tor = self.transmission.get_torrent(id)
				logging.debug("[Downloader] torrent #{0}: {1}".format(unicode(id),unicode(tor)))
				files = tor.files()
				logging.debug("[Downloader] Files of slot #{0} are {1}".format(unicode(id),files))
				result = []
				return [myFile['name'] for myFile in files.values() if myFile['selected']]
			else:
				logging.error("[Downloader] Incorrect identifier: {0}".format(unicode(id)))
				raise Exception("Incorrect identifier: {0}".format(id))
				
	def get_progression(self,id):
		if self.data['client'] == 'transmission':
			logging.debug("[Downloader] retrieving progression of slot #{0}".format(unicode(id)))
			if ( isinstance(id,basestring) ) and id.isdigit():
				id = int(id)
			if isinstance(id,int):
				if self.transmission is None:
					self._transConnect()
				tor = self.transmission.get_torrent(id)
				progression = int(tor.percentDone*100)
				logging.debug("[Downloader] Progression of slot #{0} is {1}".format(unicode(id),unicode(progression)))
				return progression
		
		
	#TransmissionRPC
	def _transConnect(self):
		if self.transmission is None:
			self.transConf = self.getValue(hidePassword=False)['transConf']
			try:
				self.transmission = transmissionrpc.Client(
										address=self.transConf['address'], 
										port=self.transConf['port'], 
										user=self.transConf['username'] if 'username' in self.transConf.keys() else '', 
										password=self.transConf['password'] if 'password' in self.transConf.keys() else ''
										)
			except:
				conf = self.getValue(hidePassword=True)['transConf']
				raise Exception("Transmission connection error {0}".format(unicode(conf)))
				
	def _transAvailableSlot(self):
		if self.data['client'] == 'transmission':
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
		return self.delete_torrent(id,delete_data=True)
		
	def delete_torrent(self,id,delete_data=True):
		if self.data['client'] == 'transmission':
			logging.info('[Downloader] Removing files from slot #{0}'.format(unicode(id)))
			self.transmission.remove_torrent(id, delete_data=delete_data)
			return id
		else:
			return id
