#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import logging
import tempfile
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
		
	def get_uri(self,endpoint="source",filename="."):
		self.checkCompleted()
		if not isinstance(endpoint,basestring) or unicode(endpoint) not in ['source','destination']:
			raise Exception("You must choose 'endpoint' parameter among 'source'/'destination'")
		endpoint = unicode(endpoint)
		data = self.data[endpoint]
		uri = URI_PATTERNS[data['protocol']].format(
			filename,
			return_if_filled('user',data),
			return_if_filled('password',data),
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
		tmpfile = unicode(tempfile.mkstemp()[1])
		os.remove(tmpfile)
		logging.info('[Transferer] Transfering file from {0} to {1}'.format(self.get_uri("source",filename),self.get_uri("destination",filename)))
		source_file = storage.get_storage(self.get_uri("source",filename))
		dest_file = storage.get_storage(self.get_uri("destination",filename))
		source_file.save_to_filename(tmpfile)
		dest_file.load_from_filename(tmpfile)
		os.remove(tmpfile)
		if delete_after:
			source_file.delete()
