# -*- coding: utf-8 -*-

import os
from gensim.corpora import WikiCorpus, MmCorpus
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from pprint import pprint
import multiprocessing

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
VERBATIMDB = os.path.join(ROOT, 'data/datasets/verbatim.sqlite')
WIKI = os.path.join(ROOT, 'data/datasets/frwiki-latest-pages-articles.xml.bz2')

#DOC2VECMAP = os.path.join(ROOT, 'data/models/wikifr_mapfile.txt')
DOC2VECMODEL = os.path.join(ROOT, 'data/models/wikifr_doc2vec200.model')

class TaggedWikiDocument(object):
    def __init__(self, wiki):
        self.wiki = wiki
        self.wiki.metadata = True
    def __iter__(self):
        for content, (page_id, title) in self.wiki.get_texts():
            yield TaggedDocument([c for c in content], [title])


wiki = WikiCorpus(WIKI)
documents = TaggedWikiDocument(wiki)

cores = multiprocessing.cpu_count()
model = Doc2Vec(
    dm=1,
    dm_mean=1,
    vector_size=200,
    window=8,
    min_count=19,
    epochs=10,
    workers=cores
   #, docvecs_mapfile=DOC2VECMAP
)

model.build_vocab(documents)
print(str(model))

model.train(documents, total_examples=model.corpus_count, epochs=model.epochs)
model.save(DOC2VECMODEL)
