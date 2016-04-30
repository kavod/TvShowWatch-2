#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import JSAG3
import logging
import smtplib
from email.mime.text import MIMEText

class Notificator(JSAG3.JSAG3):
	def __init__(self,id="notificator",dataFile=None,verbosity=False):
		curPath = os.path.dirname(os.path.realpath(__file__))
	
		JSAG3.JSAG3.__init__(self,
			id=id,
			schemaFile=curPath+"/notificator.jschem",
			optionsFile=curPath+"/notificator.jopt",
			dataFile=dataFile,
			verbosity=verbosity
		)
		
	def loadConfig(self,confFile,path=[]):
		self.addData(confFile)
		
	def send(self,title,content,dest):
		self.checkCompleted()
		if self.isValid():
			for notif in self:
				if notif['method'] == 'email':
					notif = notif['emailConf']
					logging.debug("[Notificator] Send email with parameters: {0}:{1} (SSL/TLS: {2}) user: {3} sender: '{4}' <{5}>".format(
						notif['server'],
						notif['port'],
						notif['ssltls'],
						notif['username'],
						notif['senderName'],
						notif['senderEmail']))
					msg = MIMEText(content)
					msg['Subject'] = title
					msg['From'] = notif['senderName'] if 'senderName' in notif.keys() and notif['senderName'] != "" else notif['senderEmail']
					s = smtplib.SMTP(notif['server'],notif['port'])
					if notif['ssltls']:
						s.starttls()
					s.login(notif['username'],notif['password'])
					for email in dest:
						if msg.has_key('To'):
							msg.replace_header('To', email)
						else:
							msg['To'] = email
						s.sendmail(notif['senderEmail'],email,msg.as_string())
					s.quit()
