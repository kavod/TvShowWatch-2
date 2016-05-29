#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os, sys
import datetime
import time
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
sql_select = "SELECT * FROM activity WHERE {0}"
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
        self.conn.row_factory = dict_factory

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
            myDatetime = time.mktime(datetime.datetime.now().timetuple())
        cursor = self.conn.cursor()
        cursor.execute(sql_insert_entry,(seriesid,myDatetime,oldStatus,newStatus,))
        self.conn.commit()

    def add_entries(self,entries):
        if not isinstance(entries,list) or all(not isinstance(item,dict) for item in entries):
            raise Exception("entries must be a list of dict")
        for item in entries:
            myDateTime = item['myDateTime'] if 'myDateTime' in item.keys() else None
            self.add_entry(item['seriesid'],item['oldStatus'],item['newStatus'],myDateTime)

    def get_entry(
        self,
        seriesid=None,
        oldStatus=None,
        newStatus=None,
        myDatetimeFrom=None,
        myDatetimeTo=None
    ):
        strSQL = []
        strVar = ()
        if seriesid is not None:
            strSQL.append("seriesid=?")
            strVar += (seriesid,)
        if oldStatus is not None:
            strSQL.append("oldStatus=?")
            strVar += (oldStatus,)
        if newStatus is not None:
            strSQL.append("newStatus=?")
            strVar += (newStatus,)
        cursor = self.conn.cursor()
        cursor.execute(sql_select.format(" AND ".join(strSQL)),strVar)
        return cursor.fetchall()

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d
