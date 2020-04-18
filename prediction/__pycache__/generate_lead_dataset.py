# -*- coding: utf-8 -*-

import os
import sqlite3
import pandas as pd

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
VERBATIMDB = os.path.join(ROOT, 'data/datasets/verbatim.sqlite')
LEADDATASET = os.path.join(ROOT, 'data/datasets/lead.csv')


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
    db = sqlite3.connect(db)
    with db:
        cr = db.cursor()
        records = cr.execute("SELECT id, refid, account_refid, date_entered, date_modified, title, converted, status, description FROM lead").fetchall()

    logging.info("{} Leads to process".format(len(records)))
    for r in records:
        _id, refid, account_refid, date_entered, date_modified, title, converted, status, description = r
        desc = description or ' '
        desc = ' '.join(desc.split()) or ' '
        data = {
            'refid': refid,
            'account_refid': account_refid,
            'date_entered': date_entered,
            'date_modified': date_modified,
            'title': title,
            'converted': converted,
            'status': status,
            'description': desc,
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


def dataset_iterator(db):
    it = iterator(db)
    it = map(lambda x: add_verbatim(x, db), it)
    return it


df = pd.DataFrame(dataset_iterator(VERBATIMDB))
df.to_csv(LEADDATASET, index=False)
