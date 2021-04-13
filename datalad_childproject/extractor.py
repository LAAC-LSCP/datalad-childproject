from __future__ import absolute_import
from math import isnan

# use pybids to evolve with the standard without having to track it too much
import pandas as pd
import os
import re
import numpy as np

from datalad.dochelpers import exc_str
from datalad.metadata.extractors.base import BaseMetadataExtractor
from datalad.metadata.definitions import vocabulary_id
from datalad.utils import assure_unicode
from datalad.support.external_versions import external_versions

from datalad import cfg

import logging
lgr = logging.getLogger('datalad.metadata.extractors.childproject')
from datalad.log import log_progress


vocabulary = {
    "age(months)": {
        '@id': "age",
        'unit': "month",
        'unit_label': "month",
        'description': "child age at the time of recording"}
}

content_metakey_map = {
    'child_id': 'id',
    'age': 'age(months)',
    'location_id': 'location id'
}

sex_label_map = {
    'f': 'female',
    'm': 'male',
}


class MetadataExtractor(BaseMetadataExtractor):
    def get_metadata(self, dataset, content):

        try:
            recordings = pd.read_csv(os.path.join(self.ds.path, 'metadata/recordings.csv'))
            children = pd.read_csv(os.path.join(self.ds.path, 'metadata/children.csv'))
        except Exception as exc:
            lgr.error("could not read the metadata due to some exception.\n{}".format(str(exc)))
            return {}, []

        ## Extract experiment(s)
        experiment = None
        try:
            experiments = list(recordings['experiment'].unique())
            assert len(experiments) == 1
            experiment = experiments[0]
        except Exception as exc:
            lgr.error("could not determine the experiment ({})".format(str(exc)))

        dsmeta = {
            'experiment': experiment
        }

        ## Extract sample size
        dsmeta['children'] = children.shape[0]
        dsmeta['recordings'] = recordings.dropna(subset = ['recording_filename']).shape[0]
        dsmeta['duration'] = int(recordings['duration'].sum())

        ## Extract languages
        languages = []
        if 'language' in children.columns:
            languages.extend(list(children['language'].str.strip().unique()))
        
        if 'languages' in children.columns:
            languages.extend(list(set(np.ravel(children['languages'].str.split(';').map(lambda s: s.strip()).values))))

        dsmeta['languages'] = languages

        ### Extract devices
        dsmeta['devices'] = list(recordings['recording_device_type'].dropna().unique())

        ### Vocabulary specifications
        context = {}
        context['childproject'] = {
            '@id': '#',
            'description': 'ad-hoc vocabulary for the ChildProject standard',
            'type': vocabulary_id,
        }
        context.update(vocabulary)
        dsmeta['@context'] = context

        return (dsmeta, [])