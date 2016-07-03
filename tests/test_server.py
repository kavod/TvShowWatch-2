#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import unittest
import Server

class TestServer(unittest.TestCase):
    def test_users(self):
        u = Server.Users()
        self.assertTrue(isinstance(u.index(),list))

    def test_groups(self):
        u = Server.Groups()
        self.assertTrue(isinstance(u.index(),list))
