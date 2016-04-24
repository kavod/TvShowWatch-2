#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import logging
import tempfile
import shutil
import storage
import JSAG3

'''
{0}: filename
{1}: username
{2}: password
{3}: host
{4}: port
{5}: path
{6}: auth_endpoint
{7}: tenant_id
{8}: region
{9}: public
{10}: api_key
{11}: temp_url_key
{12}: access_key
{13}: secret_key
'''

URI_PATTERNS = {
	"file":'file://{5}/{0}',
	"swift":'swift://{1}:{2}@{3}{5}/{0}?region={8}&auth_endpoint={6}&tenant_id={7}{9}{10}{11}',
	"cloud":'cloudfiles://{1}:{2}@{3}{5}/{0}?region={8}',
	"s3":'s3://{12}:{13}@{3}{5}/{0}',
	"ftp":'ftp://{1}:{2}@{3}{4}{5}/{0}',
	"ftps":'ftps://{1}:{2}@{3}{4}{5}/{0}'
}

def return_if_filled(var,data):
	if var in data.keys():
		if isinstance(data[var],int):
			if data[var]<1:
				return ''
			else:
				return unicode(data[var])
		else:
			return data[var]
	else:
		return ''

class Transferer(JSAG3.JSAG3):
	def __init__(self,id="transferer",dataFile=None,verbosity=False):
		curPath = os.path.dirname(os.path.realpath(__file__))
		JSAG3.JSAG3.__init__(self,
			id=id,
			schemaFile=curPath+"/transferer.jschem",
			optionsFile=curPath+"/transferer.jopt",
			dataFile=dataFile,
			verbosity=verbosity
		)
		
	def get_uri(self,endpoint="source",filename=".",showPassword=False):
		self.checkUsable()
		if not isinstance(endpoint,basestring) or unicode(endpoint) not in ['source','destination']:
			raise Exception("You must choose 'endpoint' parameter among 'source'/'destination'")
		endpoint = unicode(endpoint)
		data = self.data[endpoint]
		uri = URI_PATTERNS[data['protocol']].format(
			filename,
			return_if_filled('user',data),
			return_if_filled('password',data) if showPassword else '*****',
			return_if_filled('host',data),
			(':'+return_if_filled('port',data)) if return_if_filled('port',data) !='' else '',
			return_if_filled('path',data),
			return_if_filled('auth_endpoint',data),
			return_if_filled('tenant_id',data),
			return_if_filled('region',data),
			('&public=' + return_if_filled('public',data)) if return_if_filled('public',data) != '' else '',
			('&api_key=' + return_if_filled('api_key',data)) if return_if_filled('api_key',data) != '' else '',
			('&temp_url_key=' + return_if_filled('temp_url_key',data)) if return_if_filled('temp_url_key',data) != '' else '',
			return_if_filled('access_key',data),
			return_if_filled('secret_key',data)
		)
		return uri
		
	def transfer(self,filename,delete_after=False):
		logging.info('[Transferer] Transfering file from {0} to {1}'.format(self.get_uri("source",filename),self.get_uri("destination",filename)))
		
		source_file = storage.get_storage(self.get_uri("source",filename,showPassword=True))
		dest_file = storage.get_storage(self.get_uri("destination",filename,showPassword=True))
		
		if self.data['source']['protocol'] == 'file' and self.data['destination']['protocol'] == 'file':
			destination = "{0}/{1}".format(self.data['destination']['path'],filename)
			if not os.path.exists(os.path.dirname(destination)):
				os.mkdir(os.path.dirname(destination))
			shutil.copyfile("{0}/{1}".format(self.data['source']['path'],filename),destination)
		else:
			if self.data['source']['protocol'] == 'file':
				dest_file.load_from_filename("{0}/{1}".format(self.data['source']['path'],filename))
			elif self.data['destination']['protocol'] == 'file':
				destination = "{0}/{1}".format(self.data['destination']['path'],filename)
				if not os.path.exists(os.path.dirname(destination)):
					os.mkdir(os.path.dirname(destination))
				source_file.save_to_filename(destination)
			else:
				tmpfile = unicode(tempfile.mkstemp()[1])
				os.remove(tmpfile)
				source_file.save_to_filename(tmpfile)
				dest_file.load_from_filename(tmpfile)
				os.remove(tmpfile)
		if delete_after:
			source_file.delete()
		
	def delete(self,filename):
		logging.info('[Transferer] Deleting file {0}'.format(self.get_uri("source",filename)))
		source_file = storage.get_storage(self.get_uri("source",filename,showPassword=True))
		source_file.delete()
			
	def checkUsable(self):
		if 'source' not in self.data.keys() or self.data['source'] is None:
			raise Exception("Source not specified")
		if 'destination' not in self.data.keys() or self.data['source'] is None:
			raise Exception("Destination not specified")
		if 'protocol' not in self.data['source'].keys() or self.data['source']['protocol'] is None:
			raise Exception("Protocol missing for source")
		if 'path' not in self.data['source'].keys() or self.data['source']['path'] is None:
			raise Exception("Path missing for source")
		if 'protocol' not in self.data['destination'].keys() or self.data['destination']['protocol'] is None:
			raise Exception("Protocol missing for destination")
		if 'path' not in self.data['destination'].keys() or self.data['destination']['path'] is None:
			raise Exception("Path missing for destination")
