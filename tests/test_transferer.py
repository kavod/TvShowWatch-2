#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import tempfile
import shutil
import mock
import Transferer

DEBUG=False

class TestTransferer(unittest.TestCase):
	def setUp(self):
		self.tmpfiles = []
		self.tmpdirs = []
		self.tmpdirs.append(unicode(tempfile.mkdtemp()))
		self.tmpdirs.append(unicode(tempfile.mkdtemp()))
		
		self.ftp_server = "my-ftp-server"
		self.ftp_port = 12345
		self.ftp_user = "username"
		self.ftp_pwd = "password"
		self.ftp_dir = "foo/bar"
		
		self.data1 = {"source": {"path": self.tmpdirs[0], "protocol": "file"}, "destination": {"path": self.tmpdirs[1], "protocol": "file"}}
		self.data3 = {"source": {"path": self.tmpdirs[0], "protocol": "file"}, "destination": {"protocol": "ftps", "host": self.ftp_server, "user": self.ftp_user, "path": "/"+self.ftp_dir, "password": self.ftp_pwd, "port": self.ftp_port}}
		self.data4 = {"source": {"path": self.tmpdirs[0], "protocol": "file"}, "destination": {"protocol": "ftp", "host": self.ftp_server, "user": self.ftp_user, "path": "/"+self.ftp_dir, "password": self.ftp_pwd, "port": self.ftp_port}}
		
		
	def test_creation(self):
		trans = self.creation(id="test1")
		self.assertIsInstance(trans,Transferer.Transferer)
		
	def test_creation_with_data(self):
		trans = self.creation(id="test1",data=self.data1)
		self.assertIsInstance(trans,Transferer.Transferer)
		
	def test_get_uri_file(self):
		trans = self.creation(id="test4",data=self.data4)
		self.assertEquals(trans.get_uri(endpoint="source",filename="test"),"file://"+self.tmpdirs[0]+"/test")
		
	def test_get_uri_ftp(self):
		trans = self.creation(id="test4",data=self.data4)
		self.assertEquals(trans.get_uri(endpoint="destination",filename="awesome-file.txt"),"ftp://username:password@my-ftp-server:12345/foo/bar/awesome-file.txt")
		
	def test_get_uri_ftps(self):
		trans = self.creation(id="test3",data=self.data3)
		self.assertEquals(trans.get_uri(endpoint="destination",filename="awesome-file.txt"),"ftps://username:password@my-ftp-server:12345/foo/bar/awesome-file.txt")
		
	def test_transfer_file_to_file(self):
		trans = self.creation(id="test1",data=self.data1)
		tmpfile = unicode(tempfile.mkstemp('.txt',dir=self.tmpdirs[0])[1])
		self.tmpfiles.append(tmpfile)
		tmpfile = os.path.basename(tmpfile)
		self.assertFalse(os.path.isfile(self.tmpdirs[1]+"/"+tmpfile))
		trans.transfer(tmpfile)
		self.assertTrue(os.path.isfile(self.tmpdirs[0]+"/"+tmpfile))
		self.assertTrue(os.path.isfile(self.tmpdirs[1]+"/"+tmpfile))
		
	def test_transfer_file_to_file_delete_after(self):
		trans = self.creation(id="test1",data=self.data1)
		tmpfile = unicode(tempfile.mkstemp('.txt',dir=self.tmpdirs[0])[1])
		tmpfile = os.path.basename(tmpfile)
		self.assertFalse(os.path.isfile(self.tmpdirs[1]+"/"+tmpfile))
		trans.transfer(tmpfile,delete_after=True)
		self.assertFalse(os.path.isfile(self.tmpdirs[0]+"/"+tmpfile))
		self.assertTrue(os.path.isfile(self.tmpdirs[1]+"/"+tmpfile))
		
	@mock.patch("ftplib.FTP", autospec=True)
	def test_transfer_file_to_ftp(self, mock_ftp_class):
		mock_ftp = mock_ftp_class.return_value
	
		trans = self.creation(id="test4",data=self.data4)
		tmpfile = unicode(tempfile.mkstemp('.txt',dir=self.tmpdirs[0])[1])
		with open(tmpfile,'w') as outfile:
			outfile.write('niouf')
		self.tmpfiles.append(tmpfile)
		tmpfile = os.path.basename(tmpfile)
		trans.transfer(tmpfile)
		
		mock_ftp_class.assert_called_with()
		mock_ftp.connect.assert_called_with(self.ftp_server, port=self.ftp_port)
		mock_ftp.login.assert_called_with(self.ftp_user, self.ftp_pwd)
		mock_ftp.cwd.assert_called_with(self.ftp_dir)
		
		mock_ftp.storbinary.assert_called_with(
			"STOR "+tmpfile,mock_ftp.storbinary.mock_calls[0][1][1]	)
		
	def creation(self,id="test",data={}):
		tmpfile = unicode(tempfile.mkstemp('.json')[1])
		self.tmpfiles.append(tmpfile)
		os.remove(tmpfile)
		trans = Transferer.Transferer(id=id,dataFile=tmpfile,verbosity=DEBUG)
		if data != {}:
			trans.setValue(data)
		return trans
		
	def tearDown(self):
		for tmpfile in self.tmpfiles:
			os.remove(tmpfile)
		for tmpdir in self.tmpdirs:
			shutil.rmtree(tmpdir)