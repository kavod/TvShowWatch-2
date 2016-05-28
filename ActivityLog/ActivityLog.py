#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os, sys
import datetime
import sqlite3

sql_table_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
sql_create_activity_table = """
CREATE TABLE IF NOT EXISTS activity(
     id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
     seriesid INTEGER,
     datetime INTEGER,
     oldStatus INTEGER,
     newStatus INTEGER
)
"""
sql_insert_entry = """INSERT INTO activity (seriesid,datetime,oldStatus,newStatus)
    VALUES (?,?,?,?)"""

class ActivityLog(object):
    def __init__(self,filename):
        self.conn = None
        self.filename = filename
        if os.path.isfile(self.filename):
            try:
                self.conn = sqlite3.connect(self.filename)
                cursor = self.conn.cursor()
                cursor.execute(sql_table_exists,"activity")
                if cursor.rowcount() < 1:
                    self.initDb()
            except:
                self.initDb()
        else:
            self.initDb()

    def initDb(self):
        if self.conn is not None:
            self.conn.close()
        if os.path.isfile(self.filename):
            os.remove(self.filename)
        self.conn = sqlite3.connect(self.filename)
        cursor = self.conn.cursor()
        cursor.execute(sql_create_activity_table)
        self.conn.commit()

    def add_entry(self,seriesid,oldStatus,newStatus,myDatetime=None):
        if myDatetime is None:
            myDatetime = datetime.datetime.now()
        cursor = self.conn.cursor()
        cursor.execute(sql_insert_entry,(seriesid,myDatetime,oldStatus,newStatus,))
        self.conn.commit()
