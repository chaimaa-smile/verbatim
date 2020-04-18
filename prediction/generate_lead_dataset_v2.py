# -*- coding: utf-8 -*-
import configparser
import os
import sqlite3
import pandas as pd
from mysql.connector import (connection)
import mysql.connector
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
MYSQLCONF = os.path.join(ROOT, 'mysql_config.ini')
VERBATIMDB = os.path.join(ROOT, 'data/datasets/verbatim.sqlite')
LEADDATASET = os.path.join(ROOT, 'data/datasets/lead_global.csv')


VERBATIMDATA = dict()
def get_verbatims(refid, db):
    global VERBATIMDATA

    if not VERBATIMDATA:
        db = sqlite3.connect(db)
        with db:
            cr = db.cursor()
            verbatims = cr.execute("SELECT title, content, parent_refid FROM verbatim WHERE parent_refid is not null").fetchall()

        for row in verbatims:
            t, c, pid = row
            t = ' '.join(t.replace("'", " ").replace('"', " ").split())
            c = ' '.join(c.replace("'", " ").replace('"', " ").split())
            if pid not in VERBATIMDATA:
                VERBATIMDATA[pid] = [(t, c)]
            else:
                VERBATIMDATA[pid].append((t, c))
    return VERBATIMDATA.get(refid, [])


def iterator(db):
    cnx = mysql.connector.connect(**db)

    cr = cnx.cursor()
    record = cr.execute("""  select l.id as  refid,l.account_id as account_refid,a.name ,YEAR(l.date_entered) as date_entered_year,MONTH(l.date_entered) as date_entered_month,DAY(l.date_entered) as date_entered_day,
 YEAR(l.date_modified) as date_modified_year,MONTH(l.date_modified) as date_modified_month,DAY(l.date_modified) as date_modified_day,l.title,l.converted,l.status,l.description ,YEAR(max(c.date_end )) as dernier_appel_year,MONTH(max(c.date_end ) )as dernier_appel_month,DAY(max(c.date_end )) as dernier_appel_day,
              max(c.duration_minutes) as duree_appel_minutes, 
               max(c.duration_hours ) as duree_appel_heures,count(c.id) nb_appel , 
                 YEAR(max(m.date_end )) as dernier_rdv_year,MONTH(max(m.date_end )) as dernier_rdv_month,DAY(max(m.date_end )) as dernier_rdv_day,
               max(m.duration_minutes) as duree_rdv_minutes, 
               max(m.duration_hours ) as duree_rdv_heures,count(m.id) nb_rdv
               from leads l left join  accounts a on (a.id=l.account_id) left join meetings m  on (m.parent_id =l.account_id) left join calls c  on (c.parent_id =l.account_id)
                group by l.id,l.account_id,a.name ,YEAR(l.date_entered),MONTH(l.date_entered),DAY(l.date_entered),YEAR(l.date_modified),MONTH(l.date_modified),DAY(l.date_modified),
                l.title,l.converted,l.status,l.description""")

    records=cr.fetchall()
    logging.info("{} Leads to process".format(len(records)))
    for r in records:
        refid, account_refid, name,date_entered_year,date_entered_month,date_entered_day, date_modified_year ,date_modified_month ,date_modified_day, title, converted, status, description, dernier_appel_year,dernier_appel_month,dernier_appel_day, duree_appel_minutes, duree_appel_heures,nb_appel,  dernier_rdv_year,dernier_rdv_month,dernier_rdv_day, duree_rdv_minutes, duree_rdv_heures, nb_rdv  = r
        desc = description or ' '
        desc = ' '.join(desc.split()) or ' '
        data = {
            'refid': refid,
            'account_refid': account_refid,
            'name':name,
            'date_entered_year': date_entered_year,
            'date_entered_month':date_entered_month,
            'date_entered_day' :date_entered_day,
            'date_modified_year':date_modified_year,
            'date_modified_month':date_modified_month,
            'date_modified_day': date_modified_day,

            'title': title,
            'converted': converted,
            'status': status,
            'description': desc,
            'dernier_appel_year': dernier_appel_year,
            'dernier_appel_month': dernier_appel_month,
            'dernier_appel_day': dernier_appel_day,
            'duree_appel_minutes': duree_appel_minutes,
            'duree_appel_heures' :duree_appel_heures,
            'nb_appel': nb_appel,
            'dernier_rdv_year': dernier_rdv_year,
            'dernier_rdv_month': dernier_rdv_month,
            'dernier_rdv_day': dernier_rdv_day,
            'duree_rdv_minutes':duree_rdv_minutes,
            'duree_rdv_heures':duree_rdv_heures,
            'nb_rdv' :nb_rdv,
        }
        yield data


def log(x):
    index, data = x
    if index % 1000 == 0: logging.info("Processed {} leads".format(index))
    return data


def add_verbatim(data, db):
    new_data = data.copy()
    verbatims = get_verbatims(new_data['refid'], db)
    verbatim_str = ' '.join(map(lambda x: x[0] + ' ' + x[1], verbatims))
    new_data['verbatim'] = verbatim_str or ' '
    return new_data


def dataset_iterator(db,db2):
    it = iterator(db)
    it = map(lambda x: add_verbatim(x, db2), it)
    return it

def _read_conf(mysql_conf):
    if not os.path.exists(mysql_conf):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), mysql_conf)

    config = configparser.ConfigParser()
    config.read(mysql_conf)
    config_mysql = dict(config['MYSQL'])
    config_mysql['raise_on_warnings'] = config.getboolean('MYSQL', 'raise_on_warnings')
    return config_mysql

mysqlconf = _read_conf(MYSQLCONF)
df = pd.DataFrame(dataset_iterator(mysqlconf,VERBATIMDB))
df.to_csv(LEADDATASET, index=False)
