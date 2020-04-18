# -*- coding: utf-8 -*-

import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LEAD = os.path.join(ROOT, 'data/datasets/lead_global.csv')
LEADPREPARED = os.path.join(ROOT, 'data/datasets/lead_prepared_global.csv')


def load_lead_dataframe():
    return pd.read_csv(LEAD)

def load_lead_prepared_dataframe():
    return pd.read_csv(LEADPREPARED)
