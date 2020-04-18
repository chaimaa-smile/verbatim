# -*- coding: utf-8 -*-

import os
import mysql.connector
import sqlite3
import configparser

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
MYSQLCONF = os.path.join(ROOT, 'mysql_config.ini')
VERBATIMDB = os.path.join(ROOT, 'data/datasets/verbatim.sqlite')

def _read_conf(mysql_conf):
    if not os.path.exists(mysql_conf):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), mysql_conf)

    config = configparser.ConfigParser()
    config.read(mysql_conf)
    config_mysql = dict(config['MYSQL'])
    config_mysql['raise_on_warnings'] = config.getboolean('MYSQL', 'raise_on_warnings')
    return config_mysql


class DBConnection():
    """DB Connection"""
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.connection = None

    def __enter__(self):
        self.connection = mysql.connector.connect(**self.kwargs)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


class DBManager:
    def __init__(self, mysql, sqlite):
        self.mysql = mysql
        self.sqlite = sqlite
        self._sqlitedb = None

    def sqlite_db(self):
        if not self._sqlitedb:
            db = sqlite3.connect(self.sqlite)
            self._sqlitedb = db
        return self._sqlitedb

    def mysql_db(self):
        return DBConnection(**self.mysql)

    def _init_verbatim(self):
        db = self._sqlitedb
        with db:
            cr = db.cursor()
            q = """
                CREATE TABLE verbatim(
                    id INTEGER PRIMARY KEY,
                    refid TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    parent_refid TEXT NOT NULL,
                    parent_type TEXT NOT NULL,
                    type TEXT NOT NULL
                )
            """
            cr.execute(q)
            cr.execute("CREATE INDEX index_verbatim_refid ON verbatim(refid)")




    def _init_sqlite(self):
        if os.path.exists(self.sqlite):
            os.remove(self.sqlite)

        db = sqlite3.connect(self.sqlite)
        self._sqlitedb = db
        self._init_verbatim()


    def _insert_verbatims(self, cursor, v_type):
        db = self.sqlite_db()
        insert = "INSERT INTO verbatim VALUES(NULL, ?, ?, ?, ?, ?, ?)"
        with db:
            cr_sqlite = db.cursor()
            for row in cursor:
                r = list(row)[:5] + [v_type]
                cr_sqlite.execute(insert, r)

    def extract_verbatim_meetings(self):
        with self.mysql_db() as mysql_db:
            cr = mysql_db.cursor()
            q = """
                SELECT
                    id,
                    name,
                    description,
                    parent_id,
                    parent_type
                FROM meetings
                WHERE (description is not null AND description != '' AND parent_id is not null AND parent_type is not null)
            """
            cr.execute(q)
            self._insert_verbatims(cr, 'meetings')

    def extract_verbatim_calls(self):
        with self.mysql_db() as mysql_db:
            cr = mysql_db.cursor()
            q = """
                SELECT
                    id,
                    name,
                    description,
                    parent_id,
                    parent_type
                FROM calls
                WHERE (description is not null AND description != '' AND parent_id is not null AND parent_type is not null)
            """
            cr.execute(q)
            self._insert_verbatims(cr, 'calls')


    def extract_verbatim_notes(self):
        with self.mysql_db() as mysql_db:
            cr = mysql_db.cursor()
            q = """
                SELECT
                    id,
                    name,
                    description,
                    parent_id,
                    parent_type,
                    filename
                FROM notes
                WHERE (description is not null AND description != '' AND parent_id is not null AND parent_type is not null AND filename is null)
            """
            cr.execute(q)
            self._insert_verbatims(cr, 'notes')

    def _extract_verbatims(self):
        self.extract_verbatim_meetings()
        self.extract_verbatim_calls()
        self.extract_verbatim_notes()



    def extract_dataset(self):
        self._init_sqlite()
        self._extract_verbatims()

mysqlconf = _read_conf(MYSQLCONF)
dbmanager = DBManager(mysqlconf, VERBATIMDB)
dbmanager.extract_dataset()
