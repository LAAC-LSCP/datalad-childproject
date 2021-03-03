from __future__ import absolute_import
from math import isnan

# use pybids to evolve with the standard without having to track it too much
import pandas as pd
import os
import re
from datalad.dochelpers import exc_str
from datalad.metadata.extractors.base import BaseMetadataExtractor
from datalad.metadata.definitions import vocabulary_id
from datalad.utils import assure_unicode
from datalad.support.external_versions import external_versions

from datalad import cfg

import logging
lgr = logging.getLogger('datalad.metadata.extractors.childrecords')
from datalad.log import log_progress


vocabulary = {
    "age(years)": {
        '@id': "pato:0000011",
        'unit': "uo:0000036",
        'unit_label': "year",
        'description': "age of a sample (organism) at the time of data acquisition in years"},
}

content_metakey_map = {
    # go with plain 'id' as BIDS has this built-in conflict of subject/participant
    # for the same concept
    'child_id': 'id',
    'age': 'age(years)',
    'location_id': 'location id'
}

sex_label_map = {
    'f': 'female',
    'm': 'male',
}


class MetadataExtractor(BaseMetadataExtractor):
    _dsdescr_fname = 'dataset_description.json'

    _key2stdkey = {
        'Name': 'name',
        'License': 'license',
        'Authors': 'author',
        'ReferencesAndLinks': 'citation',
        'Funding': 'fundedby',
        'Description': 'description',
    }

    def get_metadata(self, dataset, content):
        dataframes = ['metadata/recordings.csv', 'metadata/children.csv']
        
        try:
            recordings = pd.read_csv('metadata/recordings.csv')
            children = pd.read_csv('metadata/children.csv')
        except Exception as exc:
            lgr.error("could not read the metadata due to some exception.\n{}".format(str(exc)))
            return {}, []

        experiment = None
        try:
            experiments = list(recordings['experiment'].unique())
            assert len(experiments) == 1
            experiment = experiments[0]
        except Exception as exc:
            lgr.error("could not determine the experiment ({})".format(str(exc)))

        dsmeta = {
            'Experiment': experiment
        }

        return (dsmeta, [])