# -*- coding: utf-8 -*-

import os
import pandas as pd
import joblib
import multiprocessing
import webbrowser
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import log_loss, make_scorer, accuracy_score
from dataset import load_lead_prepared_dataframe


scoring = {
    'accuracy': make_scorer(accuracy_score),
    'log_loss': make_scorer(log_loss)
}

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
MODEL = os.path.join(ROOT, 'data/models/lead_classifier_lr.model')
TRAINRESULTS = os.path.join(ROOT, 'data/models/lead_classifier_training_results_lr.html')


df = load_lead_prepared_dataframe()

y = df['converted']
X = df.drop('converted', axis=1)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

X_train=pd.DataFrame(X_train)
y_train=pd.DataFrame(y_train)
X_test=X_test.fillna(0)
X_train=X_train.fillna(0)
parameters = {"C":np.logspace(-3,3,7), "penalty":["l1","l2"]}

logreg = LogisticRegression()
clf = GridSearchCV(logreg, parameters, cv=10)
clf.fit(X_train, y_train)


logging.info("Training results saved to {}".format(TRAINRESULTS))


logging.info(clf)
logging.info(clf.best_estimator_)

logging.info("Saving model to {}".format(MODEL))
joblib.dump(clf.best_estimator_, MODEL)

logging.info("Scoring")
y_pred = clf.best_estimator_.predict(X_test)
acc = accuracy_score(y_pred, y_test)
loss = log_loss(y_pred, y_test)
logging.info("Accuracy : {}".format(str(acc)))
logging.info("Log Loss : {}".format(str(loss)))
