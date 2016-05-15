#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os
import tempfile
import unittest
from utils.TSWdirectories import TSWdirectories

class TestTSWdirectories(unittest.TestCase):
	def setUp(self):
		self.filename = "utils/directory_linux.conf"
		
	def test_creation(self):
		directories = TSWdirectories(self.filename)
		self.assertIsInstance(directories,TSWdirectories)
		self.assertGreater(len(directories.keys()),0)
	
	def test_directory_creation(self):
		path = tempfile.mkdtemp()
		os.rmdir(path)
		path1 = "{0}/AzErTy".format(path)
		directories = TSWdirectories()
		directories._parseLine('file_path="{0}"'.format(path1))
		self.assertTrue(os.path.isdir(path1))
		os.removedirs(path1)
		self.assertFalse(os.path.isdir(path))
