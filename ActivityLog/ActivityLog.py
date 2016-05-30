#!/usr/bin/env python
#encoding:utf-8
from __future__ import unicode_literals

import os, sys
import datetime
import time
import logging
import sqlite3

sql_table_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
sql_create_activity_table = """
CREATE TABLE IF NOT EXISTS activity(
     id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
     seriesid INTEGER,
     datetime INTEGER,
     season INTEGER,
     episode INTEGER,
     oldStatus INTEGER,
     type TEXT,
     newStatus INTEGER
)
"""
sql_select = "SELECT * FROM activity WHERE {0}"
sql_insert_entry = """INSERT INTO activity (seriesid,datetime,season,episode,oldStatus,newStatus,type)
    VALUES (?,?,?,?,?,?,?)"""

class ActivityLog(object):
    def __init__(self,filename,verbosity=None):
        self.conn = None
        self.filename = filename
        self.verbosity = verbosity
        self._setLogger()
        if os.path.isfile(self.filename):
            try:
                self.conn = sqlite3.connect(self.filename)
                cursor = self.conn.cursor()
                self.logger.info("SQL: {0} with {1}".format(sql_table_exists,("activity",)))
                cursor.execute(sql_table_exists,("activity",))
                if len(cursor.fetchall()) < 1:
                    self.logger.error("No table 'activity' exists. Creation")
                    self.initDb()
            except:
                self.logger.error("Error during database loading. Creating new one")
                self.initDb()
        else:
            self.logger.info("No database found at '{0}'. Creating new one."
                .format(self.filename))
            self.initDb()
        self.conn.row_factory = dict_factory

    def _setLogger(self):
		self.loggerName = "ActivityLog." + os.path.basename(self.filename)
		self.logger = logging.getLogger(self.loggerName)
		if self.verbosity is not None:
			if isinstance(self.verbosity,int):
				self.logger.setLevel(self.verbosity)
			if isinstance(self.verbosity,bool) and self.verbosity:
				self.logger.setLevel(logging.DEBUG)
			self.logger.debug("Verbosity is set to {0}".format(unicode(self.verbosity)))

    def initDb(self):
        if self.conn is not None:
            self.conn.close()
        if os.path.isfile(self.filename):
            os.remove(self.filename)
        self.conn = sqlite3.connect(self.filename)
        cursor = self.conn.cursor()
        self.logger.info("SQL: {0}".format(sql_create_activity_table))
        cursor.execute(sql_create_activity_table)
        self.conn.commit()

    def add_entry(self,seriesid,season,episode,oldStatus,newStatus,type,myDatetime=None):
        if myDatetime is None:
            myDatetime = time.mktime(datetime.datetime.now().timetuple())
        cursor = self.conn.cursor()
        self.logger.info("SQL: {0} with {1}".format(
            sql_insert_entry,
            unicode((seriesid,myDatetime,season,episode,oldStatus,newStatus,type,))
        ))
        cursor.execute(sql_insert_entry,(seriesid,myDatetime,season,episode,oldStatus,newStatus,type,))
        self.conn.commit()

    def add_entries(self,entries):
        if not isinstance(entries,list) or all(not isinstance(item,dict) for item in entries):
            raise Exception("entries must be a list of dict")
        for item in entries:
            myDateTime = item['myDateTime'] if 'myDateTime' in item.keys() else None
            self.add_entry(
                item['seriesid'],
                item['season'],
                item['episode'],
                item['oldStatus'],
                item['newStatus'],
                item['type'],
                myDateTime
            )

    def get_entry(
        self,
        seriesid=None,
        season = None,
        episode = None,
        oldStatus=None,
        newStatus=None,
        type=None,
        myDatetimeFrom=None,
        myDatetimeTo=None
    ):
        strSQL = []
        strVar = ()
        if seriesid is not None:
            strSQL.append("seriesid=?")
            strVar += (seriesid,)
        if season is not None:
            strSQL.append("season=?")
            strVar += (season,)
        if episode is not None:
            strSQL.append("episode=?")
            strVar += (episode,)
        if oldStatus is not None:
            strSQL.append("oldStatus=?")
            strVar += (oldStatus,)
        if newStatus is not None:
            strSQL.append("newStatus=?")
            strVar += (newStatus,)
        if type is not None:
            strSQL.append("type=?")
            strVar += (type,)
        cursor = self.conn.cursor()
        self.logger.info("SQL: {0} with {1}".format(
            sql_select.format(" AND ".join(strSQL)),
            unicode(strVar)
        ))
        cursor.execute(sql_select.format(" AND ".join(strSQL)),strVar)
        return cursor.fetchall()

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[unicode(col[0])] = row[idx]
	return d
