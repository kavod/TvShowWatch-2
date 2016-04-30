#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import unittest
import mock
import tempfile
import shutil
import json
from email.mime.text import MIMEText
import Notificator
import logging
import LogTestCase

DEBUG=False

class TestNotificator(LogTestCase.LogTestCase):
	def setUp(self):
		self.configFile1 = "tests/notificator1.json"
		with open(self.configFile1,'r') as fd:
			self.conf1 = json.load(fd)['notificator']
		self.title = "TvShowWatch test"
		self.dest=["me@home.net"]
		self.content = "This is a test email"
		
	def test_creation(self):
		self.d = Notificator.Notificator(verbosity=DEBUG)
		self.assertIsInstance(self.d,Notificator.Notificator)
		
	def test_loadConfig(self):
		self.assertTrue(os.path.isfile(self.configFile1))
		self.n = Notificator.Notificator(verbosity=DEBUG)
		self.n.loadConfig(self.configFile1)
		
	@mock.patch("smtplib.SMTP")
	def test_sendEmail(self, mock_smtp):
		self.n = Notificator.Notificator(verbosity=DEBUG)
		self.n.loadConfig(self.configFile1)
		self.n.send(title=self.title,content=self.content,dest=self.dest)
		instance = mock_smtp.return_value
		msg = MIMEText(self.content)
		msg['Subject'] = self.title
		msg['From'] = self.conf1[0]["emailConf"]["senderName"]
		msg['To'] = self.dest[0]
		self.assertEqual(instance.sendmail.call_count, 1)
		instance.sendmail.assert_called_once_with(
			self.conf1[0]["emailConf"]["senderEmail"], self.dest[0], msg.as_string())
			
