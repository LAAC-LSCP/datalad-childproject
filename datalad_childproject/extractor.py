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

from ChildProject.projects import ChildProject
from ChildProject.annotations import AnnotationManager

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
    def _load(self):
        self.project = ChildProject(self.ds.path)
        self.am = AnnotationManager(self.project)
        self.am.read()

    def _get_dsmeta(self, dataset, content):
        recordings = self.project.recordings
        children = self.project.children

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
        dsmeta['total_children'] = children.shape[0]
        dsmeta['total_recordings'] = recordings.dropna(subset = ['recording_filename']).shape[0]
        dsmeta['total_duration'] = int(recordings['duration'].sum())

        ## Extract languages
        languages = []
        if 'language' in children.columns:
            languages.extend(children['language'].str.strip().tolist())
        
        if 'languages' in children.columns:
            languages.extend(np.ravel(children['languages'].str.split(';').map(lambda s: s.strip()).tolist()))

        dsmeta['languages'] = list(set(languages))

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

        return dsmeta

    def _get_cnmeta(self, dataset, content):
        cnmeta = []
        contents = [{'path': f, 'abspath': os.path.abspath(os.path.join(self.ds.path, f))} for f in self.paths]

        annotations = self.am.annotations

        annotations['abspath'] = annotations.apply(lambda row:
            os.path.join(
                self.project.path,
                'annotations',
                row['set'],
                'converted',
                row['annotation_filename']
            ),
            axis = 1
        )
        annotations['abspath'] = annotations['abspath'].apply(os.path.abspath)
        annotations.sort_values('imported_at', inplace = True)
        annotations.drop_duplicates(
            'abspath',
            keep = 'last',
            inplace = True
        )
        annotations = annotations.merge(
            pd.DataFrame(contents),
            how = 'inner',
            left_on = 'abspath',
            right_on = 'abspath'
        )
        annotations['columns'] = annotations['abspath'].apply(lambda f:
            ','.join(pd.read_csv(f).dropna(axis=1, how='all').columns)
        )
        
        cnmeta.extend([
            (
                annotation['path'],
                {
                    'set': annotation['set'],
                    'format': annotation['format'],
                    'data': annotation['columns'],
                    'package_version': annotation['package_version'],
                    'duration': annotation['range_offset']-annotation['range_onset']
                }
            )
            for annotation in annotations.to_dict(orient = 'records')
        ])
        
        return cnmeta

    def get_metadata(self, dataset, content):
        try:
            self._load()
        except Exception as exc:
            lgr.error("could not read the metadata due to some exception.\n{}".format(str(exc)))
            return {}, []

        dsmeta = self._get_dsmeta(dataset, content)
        cnmeta = self._get_cnmeta(dataset, content) if content else []

        return (dsmeta, cnmeta)