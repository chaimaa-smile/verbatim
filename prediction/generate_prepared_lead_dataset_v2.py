# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime

import pandas as pd
from dataset import load_lead_dataframe
from gensim.models.doc2vec import Doc2Vec

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LEADDATASET = os.path.join(ROOT, 'data/datasets/lead_prepared_global.csv')
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
    it = map(lambda x: categorize(x, 'status'), it)
    print("1")
    it = map(embed_verbatim, it)
    print("2")
    it = map(lambda x: remove_feature(x, [ 'account_refid', 'title','description']), it)
    print("3")
    return it


test = load_lead_dataframe().head(200000)
df = pd.DataFrame(dataset_iterator(test))
print("vddhh")
df.to_csv(LEADDATASET, index=False)
print("yyyy")