# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime

import pandas as pd
from dataset import load_lead_dataframe
from gensim.models.doc2vec import Doc2Vec

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LEADDATASET = os.path.join(ROOT, 'data/datasets/lead_prepared_3.csv')
DOC2VECPATH = os.path.join(ROOT, 'data/models/wikifr_doc2vec200.model')
CAT = {
    'status': [
        'Converted',
        'Dead',
        'Disqualified',
        'Evanglist',
        'Identified',
        'Immediate',
        'In Process',
        'Inexploitable',
        'Lead',
        'New',
        'NotApplicable',
        'NotInteresting',
        'Recycled',
        'SQL'
    ]
}
DOC2VEC = Doc2Vec.load(DOC2VECPATH)


def log(x):
    index, data = x
    if index % 1000 == 0: logging.info("Prepared {} leads".format(index))
    return data


def categorize_date(data):
    new_data = data.copy()
    date_entered = new_data.pop('date_entered', None)
    if date_entered:
        date = datetime.fromisoformat(date_entered)
        y = date.year
        m = date.month
        d = date.day
    else:
        y = m = d = 0
    new_data['year_entered'] = y
    new_data['month_entered'] = m
    new_data['day_entered'] = d

    date_modified = new_data.pop('date_modified', None)
    if date_entered:
        date = datetime.fromisoformat(date_modified)
        y = date.year
        m = date.month
        d = date.day
    else:
        y = m = d = 0
    new_data['year_modified'] = y
    new_data['month_modified'] = m
    new_data['day_modified'] = d
    return new_data


def categorize(data, field):
    new_data = data.copy()

    cat_value = new_data.pop(field)
    cat_set = CAT[field]
    for i, key in enumerate(cat_set):
        new_data['{}_{}'.format(field, key)] = 0
    new_data['{}_{}'.format(field, cat_value)] = 1
    return new_data


def embed_verbatim(data):
    new_data = data.copy()

    verb = new_data.pop('verbatim', '')
    if isinstance(verb, float):
        verb = ''
    verbatim_vec = DOC2VEC.infer_vector(verb.split())
    for i, v in enumerate(verbatim_vec):
        new_data['verbatim_{}'.format(i)] = v



    return new_data


def remove_feature(data, fields):
    new_data = data.copy()
    for f in fields:
        new_data.pop(f, None)
    return new_data


def dataset_iterator(df):
    it = iter(df.to_dict(orient='records'))
    it = map(log, enumerate(it))
    it = map(categorize_date, it)
    it = map(lambda x: categorize(x, 'status'), it)
    it = map(embed_verbatim, it)
    it = map(lambda x: remove_feature(x, [ 'account_refid', 'title']), it)
    return it


test = load_lead_dataframe()
df = pd.DataFrame(dataset_iterator(test))
df.to_csv(LEADDATASET, index=False)
