# -*- coding: utf-8 -*-

import argparse
import sys
import os
import configparser
import logging
import mysql.connector
import errno
import sqlite3
import math
import json

from whoosh import index
from whoosh.fields import TEXT, Schema
from whoosh.qparser import QueryParser, OrGroup, MultifieldParser

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

ROOT = os.path.dirname(os.path.realpath(__file__))
DATAFILE = os.path.join(ROOT, 'data/query')
DATABASE = os.path.join(DATAFILE, 'verbatim.sqlite')
MYSQL_CONFIG = os.path.join(ROOT, 'mysql_config.ini')
INDEX = os.path.join(DATAFILE, 'verbatim_index')
FORMAT = 'minimal'
NUMBER = '10'

class VerbatimCLI(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Query most relevant verbatim',
            usage='''verbatim <command> [<args>]

The most commonly used verbatim commands are:
   extract     Extract verbatim from sugarcrm into a verbatim database
   index       Index verbatim from a verbatim database into an Index
   score       Update verbatim database with matching score of a query against the Index
   read        Read the most relevant verbatim from a verbatim database
   query       Query the most relevant verbatim from sugarcrm
'''
        )
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)

        getattr(self, args.command)()

    def extract(self):
        parser = argparse.ArgumentParser(description='Extact verbatim into a database')
        parser.add_argument('mysql', type=str, help="MySQL database configuration")
        parser.add_argument('database', type=str, help="Verbatim database path")
        args = parser.parse_args(sys.argv[2:])
        print(os.path.exists(args.database))
        mysql_conf = self._read_conf(args.mysql)
        self._extract(mysql_conf, args.database)


    def index(self):
        parser = argparse.ArgumentParser(description='Index verbatim')
        parser.add_argument('database',  type=str, help="Verbatim database path")
        parser.add_argument('index', type=str, help="Verbatim index path")
        args = parser.parse_args(sys.argv[2:])
        self._index(args.database, args.index)

    def score(self):
        parser = argparse.ArgumentParser(description='Score verbatim against query')
        parser.add_argument('database',  type=str, help="Verbatim database path")
        parser.add_argument('index', type=str, help="Verbatim index path")
        parser.add_argument('query', type=str, help="Query to match against")
        args = parser.parse_args(sys.argv[2:])
        self._score(args.database, args.index, args.query)

    def read(self):
        parser = argparse.ArgumentParser(description='Read most relevant verbatim')
        parser.add_argument('database',  type=str, help="Verbatim database path")
        parser.add_argument('-f', '--format', type=str,
                            default=FORMAT,
                            help="Report format",
                            choices=['minimal', 'extended', 'full'])
        parser.add_argument('-n', '--number', type=int,
                            default=NUMBER,
                            help="Number of match to report")
        args = parser.parse_args(sys.argv[2:])
        self._read(args.database, args.format, args.number)

    def query(self):
        parser = argparse.ArgumentParser(description='Read most relevant verbatim against a query')
        parser.add_argument('query', type=str, help="Query to match against")
        parser.add_argument('-d', '--database', type=str,
                            default=DATABASE,
                            help="Verbatim database path")
        parser.add_argument('-i', '--index',  type=str,
                            default=INDEX,
                            help="Verbatim database path")
        parser.add_argument('-m', '--mysql',
                            default=MYSQL_CONFIG,
                            help="MySQL database configuration")
        parser.add_argument('-f', '--format', type=str,
                            default=FORMAT,
                            help="Report format",
                            choices=['minimal', 'extended', 'full'])
        parser.add_argument('-n', '--number', type=int,
                            default=NUMBER,
                            help="Number of match to report")
        args = parser.parse_args(sys.argv[2:])
        mysql = self._read_conf(args.mysql)
        self._query(args.query, args.database, args.index, mysql, args.format, args.number)

    def _read_conf(self, mysql_conf):
        if not os.path.exists(mysql_conf):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), mysql_conf)

        config = configparser.ConfigParser()
        config.read(mysql_conf)
        config_mysql = dict(config['MYSQL'])
        config_mysql['raise_on_warnings'] = config.getboolean('MYSQL', 'raise_on_warnings')
        return config_mysql

    @staticmethod
    def _extract(mysql, sqlite):
        LOGGER.info('Running verbatim extract, MySQL={}, Database={}'.format(mysql, sqlite))
        dbmanager = DBManager(mysql, sqlite)
        dbmanager.extract_verbatims()

    @staticmethod
    def _index(sqlite, index):
        LOGGER.info('Running verbatim index, Database={}, Index={}'.format(sqlite, index))
        indexmanager = Index(index, sqlite)
        indexmanager.init_index()
        indexmanager.index_verbatims()

    @staticmethod
    def _score(sqlite, index, query):
        LOGGER.info('Running scoring, Database={}, Index={}, Query={}'.format(sqlite, index, query))
        indexmanager = Index(index, sqlite)
        indexmanager.load_index()
        indexmanager.clean_score()
        indexmanager.score(query)

    @staticmethod
    def _read(sqlite, format, number):
        LOGGER.info('Running reporting, Database={}, Format={}, Number={}'.format(sqlite, format, number))
        dbmanager = DBManager(None, sqlite)
        dbmanager.read(format, number)

    def _query(self, query, sqlite, index, mysql, format, number):
        self._extract(mysql, sqlite)
        self._index(sqlite, index)
        self._score(sqlite, index, query)
        self._read(sqlite, format, number)


class DBConnection:
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
                    type TEXT NOT NULL,
                    parent_refid TEXT NOT NULL,
                    parent_type TEXT NOT NULL,
                    score REAL)
            """
            cr.execute(q)
            cr.execute("CREATE INDEX index_refid ON verbatim(refid)")

    def _init_sqlite(self):
        if os.path.exists(self.sqlite):
            os.remove(self.sqlite)

        db = sqlite3.connect(self.sqlite)
        self._sqlitedb = db
        self._init_verbatim()

    def _insert_verbatims(self, cursor, v_type):
        db = self.sqlite_db()
        q = "INSERT INTO verbatim VALUES(NULL, ?, ?, ?, '{}', ?, ?, NULL)".format(v_type)
        with db:
            cr = db.cursor()
            for row in cursor:
                cr.execute(q, row[:5])

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

    def extract_verbatims(self):
        self._init_sqlite()
        LOGGER.info("Extracting meetings verbatim")
        self.extract_verbatim_meetings()
        LOGGER.info("Extracting calls verbatim")
        self.extract_verbatim_calls()
        LOGGER.info("Extracting notes verbatim")
        self.extract_verbatim_notes()

    def read_iterator(self):
        db = self.sqlite_db()
        q = """
            SELECT
                parent_refid,
                parent_type,
                refid,
                title,
                content,
                type,
                score
            FROM verbatim
            ORDER BY score desc
        """
        with db:
            cr = db.cursor()
            cr.execute(q)
            return map(
                lambda r: {
                    'parent_refid': r[0],
                    'parent_type': r[1],
                    'refid': r[2],
                    'title': r[3],
                    'content': r[4],
                    'type': r[5],
                    'score': r[6] or 0
                }, cr)

    def group(self, iterator):
        groups = dict()
        for v in iterator:
            refid = v['parent_refid']
            if refid in groups:
                groups[refid].append(v)
            else:
                groups[refid] = [v]

        report = []
        for refid, verbatims in groups.items():
            record = {
                'refid': refid,
                'type': verbatims[0]['parent_type'],
                'score': sum(map(lambda x: x['score'], verbatims)),
                'verbatim': list(sorted(verbatims, reverse=True, key=lambda x: x['score']))
            }
            report.append(record)

        return list(sorted(report, reverse=True, key=lambda x: x['score']))

    def format_report(self, report, format):
        if format == 'minimal':
            for r in report:
                r.pop('verbatim', None)
        elif format == 'extended':
            for r in report:
                r['verbatim'] = list(filter(lambda x: x['score'] != 0, r['verbatim']))
        elif format == 'full':
            pass

    def read(self, format, number):
        iterator = self.read_iterator()
        report = self.group(iterator)
        self.format_report(report, format)
        print(json.dumps(report[:number], indent=4))

class Index:
    def __init__(self, indexdir, sqlite):
        self.indexdir = indexdir
        self.sqlite = sqlite
        self._sqlitedb = None

    def sqlite_db(self):
        if not self._sqlitedb:
            db = sqlite3.connect(self.sqlite)
            self._sqlitedb = db
        return self._sqlitedb
        self.ix = None

    def init_index(self):
        schema = Schema(refid=TEXT(stored=True), title=TEXT(stored=True), content=TEXT)
        if not os.path.exists(self.indexdir):
            os.mkdir(self.indexdir)
        self.ix = index.create_in(self.indexdir, schema)
        return self.ix

    def load_index(self):
        self.ix = index.open_dir(self.indexdir)
        return self.ix

    def index_verbatims(self):
        writer = self.ix.writer()
        db = self.sqlite_db()
        with db:
            q = """
                SELECT
                    refid,
                    title,
                    content
                FROM verbatim
            """
            cr = db.cursor()
            cr.execute(q)
            for row in cr:
                refid, title, content = row
                writer.add_document(refid=refid, title=title, content=content)
            writer.commit()

    def score_verbatim(self, refid, score):
        q = """
            UPDATE verbatim SET score = {} WHERE refid = '{}'
        """.format(score, refid)
        db = self.sqlite_db()
        with db:
            cr = db.cursor()
            cr.execute(q)

    def clean_score(self):
        db = self.sqlite_db()
        with db:
            cr = db.cursor()
            cr.execute("UPDATE verbatim SET score = NULL")

    def score(self, query):
        ix = self.ix
        qp = MultifieldParser(["content", "title"], schema=ix.schema, group=OrGroup)
        q = qp.parse(query)

        with ix.searcher() as searcher:
            l = len(searcher.search(q))
            n = 20
            for idx in range(1, math.ceil(l / n) + 1):
                results = searcher.search_page(q, idx, n)
                for r in results:
                    self.score_verbatim(r['refid'], r.score)


if __name__ == '__main__':
    VerbatimCLI()