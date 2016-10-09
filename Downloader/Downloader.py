#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os, sys
import requests
import transmissionrpc
import logging
import JSAG3
import torrentFunctions
import shutil

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
		self._synoSid = None
		self.verbosity = verbosity

		self._setLogger(self.getClient())
		self.logger.info("Creation of Downloader from {0}".format(dataFile))

	def __setitem__(self,key,value):
		JSAG3.JSAG3.__setitem__(self,key,value)
		if key == 'client':
			pass
			self._setLogger(self.getClient())

	def getClient(self):
		if 'client' not in self.keys():
			return 'none'
		else:
			return self['client']

	def connect(self):
		if self.getClient() == 'transmission':
			self._transConnect()
		elif self.getClient() == 'synology':
			self._synoConnect()
		elif self.getClient() == 'none':
			pass

	def availableSlot(self):
		if self.getClient() == 'transmission':
			return self._transAvailableSlot()
		elif self.getClient() == 'synology':
			return self._synoAvailableSlot()
		elif self.getClient() == 'none':
			return True

	def clean(self):
		if self.getClient() == 'transmission':
			self._transClean()
		elif self.getClient() == 'synology':
			self._synoClean()
		elif self.getClient() == 'none':
			pass

	def _addTorrent(self,filename,paused=False):
		self.logger.debug("_addTorrent called for {0}".format(filename))
		tor = ''
		if self.getClient() == 'transmission':
			try:
				tor = self.transmission.add_torrent('file://{0}'.format(filename),paused=paused).id
			except transmissionrpc.TransmissionError as e:
				self.logger.error("Torrent file {0} corrupted on {1} ({2})".format(filename,self.getClient(),unicode(e)))
				raise DownloaderCorruptedTorrent(client=self.getClient(),torrentFile=filename,original=e)
		elif self.getClient() == 'synology':
			tor = self._synoAddTorrents(filename,paused=paused)
		return tor

	def getTorrent(self,id):
		if self.getClient() == 'transmission':
			return self.transmission.get_torrent(id)
		elif self.getClient() == 'synology':
			return self._synoGetTorrent(id)
		elif self.getClient() == 'none':
			return {"status":"seeding"}

	def isConnected(self):
		if self.getClient() == 'transmission':
			return (self.transmission is None)
		elif self.getClient() == 'synology':
			return (self._synoSid is None)
		elif self.getClient() == 'none':
			return True

	def checkID(self,id):
		if self.getClient() == 'transmission':
			if ( isinstance(id,basestring) ) and id.isdigit():
				id = int(id)
			if isinstance(id,int):
				return id
		elif self.getClient() == 'synology':
			if isinstance(id,basestring):
				return id
		elif self.getClient() == 'none':
			return ''
		self.logger.error("Incorrect identifier: {0}".format(unicode(id)))
		raise Exception("Incorrect identifier: {0}".format(id))

	def loadConfig(self,confFile,path=[]):
		self.addData(confFile)

	def add_torrent(self,tor,delTorrent=True):
		if delTorrent is not True:
			self.logger.warning("delTorrent parameter is depreciate since it is now part of the configuration. Ignoring")
		self.logger.info('Add_torrent method called, client is {0}'.format(self.getClient()))
		if not self.availableSlot():
			self.clean()
		try:
			result = self._addTorrent(tor,paused=False)
		except DownloaderNoSlotFound as e:
			self.logger.error("No slot found after adding torrent: {0}".format(e.args))
			if delTorrent:
				os.remove(tor)
			return -1
		# except Exception as e:
		# 	self.logger.error("Unexpected error when adding torrent: {0}".format(e.args))
		# 	if delTorrent:
		# 		os.remove(tor)
		# 	return -1

		if 'deleteAfter' not in self.keys() or self['deleteAfter']:
			os.remove(tor)
		else:
			shutil.move(tor,self['torrentFolder'])
		return unicode(result)

	def start_torrent(self,id):
		self.logger.info('Start_torrent method called, client is {0}'.format(self.getClient()))
		id = self.checkID(id)
		self.logger.debug("Starting slot #{0}".format(unicode(id)))
		if self.isConnected():
			self.connect()
		if self.getClient() == 'transmission':
			try:
				tor = self.getTorrent(id)
			except AttributeError as e:
				self.logger.error('Start torrent failed with Transmission.')
				raise DownloaderSlotNotExists(downloader_id=id,client=self.getClient(),original=e)
			tor.start()
		elif self.getClient() == 'synology':
			result = self._synoStart(id)
			if result['error'] != 0:
				self.logger.error(
					'Start torrent failed with Synology. Return code: {0}'
					.format(unicode(result['error']))
				)
				raise DownloaderSlotNotExists(downloader_id=id,client=self.getClient(),original=None)
		elif self.getClient() == 'none':
			pass

	def get_status(self,id):
		self.logger.debug("Client is {0}".format(self.getClient()))
		id = self.checkID(id)
		self.logger.debug("Retrieving status of slot #{0}".format(unicode(id)))
		if self.isConnected():
			self.connect()
		tor = self.getTorrent(id)
		if hasattr(tor,'status'):
			status = tor.status
		else:
			status = tor['status']
		self.logger.debug("Torrent #{0}: {1}".format(unicode(id),unicode(tor)))
		self.logger.debug("Status of slot #{0} is {1}".format(unicode(id),status))
		return status

	def get_files(self,id):
		self.logger.debug("Client is {0}".format(self.getClient()))
		id = self.checkID(id)
		self.logger.debug("Retrieving files of slot #{0}".format(unicode(id)))
		if self.isConnected():
			self.connect()
		if self.getClient() == 'transmission':
			tor = self.transmission.get_torrent(id)
			self.logger.debug("Torrent #{0}: {1}".format(unicode(id),unicode(tor)))
			files = tor.files()
			self.logger.debug("Files of slot #{0} are {1}".format(unicode(id),files))
			return [myFile['name'] for myFile in files.values() if myFile['selected']]
		elif self.getClient() == 'synology':
			tor = self._synoGetTorrent(id)
			self.logger.debug("Torrent #{0}: {1}".format(unicode(id),unicode(tor)))
			files = tor['additional']['file']
			self.logger.debug("Files of slot #{0} are {1}".format(unicode(id),files))
			return [myFile['filename'] for myFile in files]
		elif self.getClient() == 'none':
			return []

	def get_progression(self,id):
		id = self.checkID(id)
		self.logger.debug("Retrieving progression of slot #{0}".format(unicode(id)))
		if self.isConnected():
			self.connect()
		if self.getClient() == 'transmission':
			tor = self.transmission.get_torrent(id)
			progression = int(tor.percentDone*100)
			self.logger.debug("Progression of slot #{0} is {1}".format(unicode(id),unicode(progression)))
			return progression
		elif self.getClient() == 'synology':
			tor = self._synoGetTorrent(id)
			progression = int(tor['additional']['transfer']['size_downloaded'])*100/int(tor['size'])
			self.logger.debug("Progression of slot #{0} is {1}".format(unicode(id),unicode(progression)))
			return progression
		elif self.getClient() == 'none':
			return 100

	def delete_torrent(self,id,delete_data=True):
		id = self.checkID(id)
		self.logger.debug("Retrieving progression of slot #{0}".format(unicode(id)))
		if self.isConnected():
			self.connect()
		self.logger.info('Removing files from slot #{0}'.format(unicode(id)))
		if self.getClient() == 'transmission':
			self.transmission.remove_torrent(id, delete_data=delete_data)
			return id
		elif self.getClient() == 'synology':
			params = {
				"api":"SYNO.DownloadStation.Task",
				"version":1,
				"method":"delete",
				"id":id,
				"sid":self._synoSid
			}
			req = self._synoRequest(
				path='/webapi/DownloadStation/task.cgi',
				params=params
			)
			return req.json()[0]['id']
		else:
			return id

	#TransmissionRPC
	def _transUri(self):
		if 'ssltls' not in self.transConf.keys():
			self.transConf['ssltls'] = False
		if 'path' not in self.transConf.keys():
			self.transConf['path'] = "/transmission/rpc"
		protocol = 'https' if self.transConf['ssltls'] else 'http'
		uri = "{0}://{1}:{2}{3}".format(
			protocol,
			self.transConf['address'],
			unicode(self.transConf['port']),
			self.transConf['path']
		)
		self.logger.debug("URI of transmission is {0}".format(uri))
		return uri

	def _transConnect(self):
		if self.transmission is None:
			self.transConf = self.getValue(hidePassword=False)['transConf']
			try:
				self.transmission = transmissionrpc.Client(
										address=self._transUri(),
										#address=self.transConf['address'],
										#port=self.transConf['port'],
										user=self.transConf['username'] if 'username' in self.transConf.keys() else '',
										password=self.transConf['password'] if 'password' in self.transConf.keys() else ''
										)
			except transmissionrpc.TransmissionError as e:
				originalException = e.original
				self.logger.error(
					"TransmissionError: unable to connect '{0}' (return: {1})"
					.format(originalException.url,originalException.code)
				)
				raise DownloaderConnectionError(
					"Connection error by transmission",
					originalException.url,
					originalException.code,
					"Transmission",
					e
				)

	def _transAvailableSlot(self):
		if self.getClient() == 'transmission':
			try:
				if self.transmission is None:
					self._transConnect()
				tor = self.transmission.get_torrents()
			except transmissionrpc.TransmissionError as e:
				originalException = e.original
				self.logger.error(
					"TransmissionError: unable to connect '{0}' (return: {1})"
					.format(originalException.url,originalException.code)
				)
				raise DownloaderConnectionError(
					"Connection error by transmission",
					originalException.url,
					originalException.code,
					"Transmission",
					e
				)
			return len(tor)+1 <= self.transConf['maxSlots']
		else:
			return True

	def _transClean(self):
		try:
			self.logger.info('[Downloader] Max slots reached, removing 1 achieved torrent with {0} method'.format(self.transConf['cleanMethod']))
			torrents = self.transmission.get_torrents()
			torrents = [ tor for tor in torrents if tor.status == 'seeding']
			if self.transConf['cleanMethod'] == 'oldest':
				torrents = sorted(torrents, key=lambda tor: tor.date_added)
			elif self.transConf['cleanMethod'] == 'sharest':
				torrents = sorted(torrents, key=lambda tor: tor.uploadRatio,reverse=True)
			else:
				raise Exception("Unknown clean method: {0}".format(unicode(self.transConf['cleanMethod'])))
			self.logger.info('[Downloader] {0} torrent eligible for cleaning: {1}'.format(len(torrents),torrents))
			if len(torrents)<1:
				raise Exception("No eligible torrent for cleaning")
			id = torrents[0].id
			return self.delete_torrent(id,delete_data=True)
		except transmissionrpc.TransmissionError as e:
			originalException = e.original
			self.logger.error(
				"TransmissionError: unable to connect '{0}' (return: {1})"
				.format(originalException.url,originalException.code)
			)
			raise DownloaderConnectionError(
				"Connection error by transmission",
				originalException.url,
				originalException.code,
				"Transmission",
				e
			)

	#Synology
	def _synoRequest(self,path,params,method='GET',files=None):
		protocol = "https" if self['synoConf']['ssl'] else 'http'
		verify = self['synoConf']['ssl'] and not self['synoConf']['sslNoCheck']
		url = "https://{0}:{1}{2}".format(
			self['synoConf']['address'],
			unicode(self['synoConf']['port']),
			path
			)
		try:
			if method=='POST':
				if files is None:
					req = requests.post(url,params=params,verify=verify)
				else:
					req = requests.post(url,data=params,files=files,verify=verify)
			else:
				req = requests.get(url,params=params,verify=verify)
			if req.status_code != 200:
				self.logger.error(
					"SynologyDS: unable to connect '{0}' (return: {1})"
					.format(url,req.status_code)
				)
				raise DownloaderConnectionError(
					"Connection error by SynologyDS",
					url,
					client="SynologyDS",
					code=req.status_code
				)
			return req
		except requests.exceptions.RequestException as e:
			self.logger.error(
				"SynologyDS: unable to connect '{0}'"
				.format(url)
			)
			raise DownloaderConnectionError(
				"Connection error by SynologyDS",
				url,
				client="SynologyDS",
				original=e
			)

	def _synoConnect(self):
		if self._synoSid is None:
			params = {
				"api":"SYNO.API.Auth",
				"version":2,
				"method":"login",
				"session":"DownloadStation",
				"format":"cookie",
				"account":self['synoConf']['username'],
				"passwd":self['synoConf']['password']
			}
			req = self._synoRequest(
				path='/webapi/auth.cgi',
				params=params
			)
			response = req.json()
			if response['success']:
				self._synoSid = response['data']['sid']
			else:
				print("FAILED!")

	def _synoGetTorrents(self):
		if self.getClient() == 'synology':
			if self._synoSid is None:
				self._synoConnect()
			if self._synoSid is None:
				return []
			params = {
				"api":"SYNO.DownloadStation.Task",
				"version":1,
				"method":"list",
				"session":"DownloadStation",
				"additional":"detail,transfer,file",
				"_sid":self._synoSid
			}
			req = self._synoRequest(
				path='/webapi/DownloadStation/task.cgi',
				params=params
			)
			return req.json()['data']['tasks']
		else:
			return []

	def _synoGetTorrent(self,id):
		if self.getClient() == 'synology':
			torrents = [tor for tor in self._synoGetTorrents() if tor['id'] == id]
			if len(torrents)>0:
				return torrents[0]
			else:
				return {}
		else:
			return {}

	def _synoStart(self,id):
		if self.getClient() == 'synology':
			if self._synoSid is None:
				return []
			params = {
				"api":"SYNO.DownloadStation.Task",
				"version":1,
				"method":"resume",
				"session":"DownloadStation",
				"_sid":self._synoSid,
				"id": id
			}
			req = self._synoRequest(
				path='/webapi/DownloadStation/task.cgi',
				params=params
			)
			return req.json()['data'][0]


	def _synoAddTorrents(self,filename,paused=False):
		if paused:
			self.logger.warning("Download Station for Synology does not manage creation of paused task. Ignoring paused parameter")
		if self.getClient() == 'synology':
			if self._synoSid is None:
				return []
			params = {
				"api":"SYNO.DownloadStation.Task",
				"version":1,
				"method":"create",
				"session":"DownloadStation",
				"_sid":self._synoSid
			}
			torList = self._synoGetTorrents()
			torIDList1 = [tor['id'] for tor in torList]
			# Look for duplicates
			id = self._synoFindDuplicates(torList,filename)
			if id is None:
				with open(filename,'rb') as payload:
					files = {'file':(filename,payload)}
					req = self._synoRequest(
						path='/webapi/DownloadStation/task.cgi',
						params=params,
						method='POST',
						files = files
					)
				torIDList2 = [tor['id'] for tor in self._synoGetTorrents() if unicode(tor['id']) not in torIDList1]
				if len(torIDList2) == 1:
					return torIDList2[0]
				else:
					raise DownloaderNoSlotFound(client=self.getClient(),torrentFile=filename)
			else:
				return id

	def _synoAvailableSlot(self):
		if self.getClient() == 'synology':
			if self._synoSid is None:
				self._synoConnect()
			tor = self._synoGetTorrents()
			return len(tor)+1 <= self['synoConf']['maxSlots']
		else:
			return True

	def _synoClean(self):
		self.logger.info('Max slots reached, removing 1 achieved torrent with {0} method'.format(self['synoConf']['cleanMethod']))
		torrents = self._synoGetTorrents()
		torrents = [ tor for tor in torrents if tor['status'] == 'finished']
		if self['synoConf']['cleanMethod'] == 'oldest':
			torrents = sorted(torrents, key=lambda tor: tor['additional']['detail']['create_time'])
		elif self['synoConf']['cleanMethod'] == 'sharest':
			torrents = sorted(torrents, key=lambda tor: tor['additional']['transfer']['size_uploaded'] / tor['additional']['transfer']['size_downloaded'],reverse=True)
		else:
			raise Exception("Unknown clean method: {0}".format(unicode(self.synoConf['cleanMethod'])))
		self.logger.info('{0} torrent eligible for cleaning: {1}'.format(len(torrents),torrents))
		if len(torrents)<1:
			raise Exception("No eligible torrent for cleaning")
		id = torrents[0].id
		return self.delete_torrent(id,delete_data=True)

	def _synoFindDuplicates(self,tasksList,filename):
		data = open(filename, "rb").read()
		torrent = torrentFunctions.decode(data)
		for task in tasksList:
			if all(
				len(
					[taskFile for taskFile in task['additional']['file']
					if taskFile['filename'] == "/".join(torFile["path"]) and int(taskFile['size']) == int(torFile['length'])]
				)>0
				for torFile in torrent["info"]["files"]
			):
				return task['id']
		return None

class DownloaderConnectionError(OSError):
	def __init__(self,message='',url='',code=0,client='',original=None):
		exc_type, exc_obj, exc_tb = sys.exc_info()
		if exc_tb is not None:
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			fline = exc_tb.tb_lineno
		else:
			fname = __file__
			fline = 0
		msg = "{0} - {1} - {2} (return: {3}) [{4}:{5}]".format(
			unicode(message),
			unicode(url),
			unicode(client),
			unicode(code),
			fname,
			fline
		)
		super(OSError,self).__init__(msg)
		self.message = msg
		self.url = url
		self.code = code
		self.original = original
		self.client = client

class DownloaderSlotNotExists(KeyError):
	def __init__(self,downloader_id='',client='',original=None):
		msgSource = ''
		if original is not None:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			if exc_tb is not None:
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				fline = exc_tb.tb_lineno
			else:
				fname = __file__
				fline = 0
			msgSource = fname + ":" + unicode(fline)
		msg = "Slot {0} not exists on {1} ({2})".format(unicode(downloader_id),client,msgSource)
		super(KeyError,self).__init__(msg)
		self.message = msg
		self.original = original
		self.client = client

class DownloaderNoSlotFound(KeyError):
	def __init__(self,client='',torrentFile='',original=None):
		msgSource = ''
		if original is not None:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			if exc_tb is not None:
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				fline = exc_tb.tb_lineno
			else:
				fname = __file__
				fline = 0
			msgSource = fname + ":" + unicode(fline)
		msg = "No slot assigned when adding torrent {0} on {1} ({2})".format(unicode(torrentFile),client,msgSource)
		super(KeyError,self).__init__(msg)
		self.message = msg
		self.original = original
		self.client = client

class DownloaderCorruptedTorrent(KeyError):
	def __init__(self,client='',torrentFile='',original=None):
		msgSource = ''
		if original is not None:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			if exc_tb is not None:
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				fline = exc_tb.tb_lineno
			else:
				fname = __file__
				fline = 0
			msgSource = fname + ":" + unicode(fline)
		msg = "Torrent {0} seems corrupted on {1} ({2})".format(unicode(torrentFile),client,msgSource)
		super(KeyError,self).__init__(msg)
		self.message = msg
		self.original = original
		self.client = client
