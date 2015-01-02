# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest2


class Test_get_connection(unittest2.TestCase):

    def _callFUT(self):
        from gcloud.datastore import get_connection
        return get_connection()

    def test_it(self):
        from gcloud import credentials
        from gcloud.datastore.connection import Connection
        from gcloud.test_credentials import _Client
        from gcloud._testing import _Monkey

        client = _Client()
        with _Monkey(credentials, client=client):
            found = self._callFUT()
        self.assertTrue(isinstance(found, Connection))
        self.assertTrue(found._credentials is client._signed)
        self.assertTrue(client._get_app_default_called)


class Test_set_default_dataset(unittest2.TestCase):

    def setUp(self):
        from gcloud.datastore import _implicit_environ
        self._replaced_dataset = _implicit_environ.DATASET
        _implicit_environ.DATASET = None

    def tearDown(self):
        from gcloud.datastore import _implicit_environ
        _implicit_environ.DATASET = self._replaced_dataset

    def _callFUT(self, dataset_id=None):
        from gcloud.datastore import set_default_dataset
        return set_default_dataset(dataset_id=dataset_id)

    def _test_with_environ(self, environ, expected_result, dataset_id=None):
        import os
        from gcloud._testing import _Monkey
        from gcloud import datastore
        from gcloud.datastore import _implicit_environ

        # Check the environment is unset.
        self.assertEqual(_implicit_environ.DATASET, None)

        def custom_getenv(key):
            return environ.get(key)

        def custom_get_dataset(local_dataset_id):
            return local_dataset_id

        with _Monkey(os, getenv=custom_getenv):
            with _Monkey(datastore, get_dataset=custom_get_dataset):
                self._callFUT(dataset_id=dataset_id)

        self.assertEqual(_implicit_environ.DATASET, expected_result)

    def test_set_from_env_var(self):
        from gcloud.datastore import _DATASET_ENV_VAR_NAME

        # Make a custom getenv function to Monkey.
        DATASET = 'dataset'
        VALUES = {
            _DATASET_ENV_VAR_NAME: DATASET,
        }
        self._test_with_environ(VALUES, DATASET)

    def test_no_env_var_set(self):
        self._test_with_environ({}, None)

    def test_set_explicit(self):
        DATASET_ID = 'DATASET'
        self._test_with_environ({}, DATASET_ID, dataset_id=DATASET_ID)


class Test_set_default_connection(unittest2.TestCase):

    def setUp(self):
        from gcloud.datastore import _implicit_environ
        self._replaced_connection = _implicit_environ.CONNECTION
        _implicit_environ.CONNECTION = None

    def tearDown(self):
        from gcloud.datastore import _implicit_environ
        _implicit_environ.CONNECTION = self._replaced_connection

    def _callFUT(self, connection=None):
        from gcloud.datastore import set_default_connection
        return set_default_connection(connection=connection)

    def test_set_explicit(self):
        from gcloud.datastore import _implicit_environ

        self.assertEqual(_implicit_environ.CONNECTION, None)
        fake_cnxn = object()
        self._callFUT(connection=fake_cnxn)
        self.assertEqual(_implicit_environ.CONNECTION, fake_cnxn)

    def test_set_implicit(self):
        from gcloud._testing import _Monkey
        from gcloud import datastore
        from gcloud.datastore import _implicit_environ

        self.assertEqual(_implicit_environ.CONNECTION, None)

        fake_cnxn = object()
        with _Monkey(datastore, get_connection=lambda: fake_cnxn):
            self._callFUT()

        self.assertEqual(_implicit_environ.CONNECTION, fake_cnxn)


class Test_get_dataset(unittest2.TestCase):

    def _callFUT(self, dataset_id):
        from gcloud.datastore import get_dataset
        return get_dataset(dataset_id)

    def test_it(self):
        from gcloud import credentials
        from gcloud.datastore.connection import Connection
        from gcloud.datastore.dataset import Dataset
        from gcloud.test_credentials import _Client
        from gcloud._testing import _Monkey

        DATASET_ID = 'DATASET'
        client = _Client()
        with _Monkey(credentials, client=client):
            found = self._callFUT(DATASET_ID)
        self.assertTrue(isinstance(found, Dataset))
        self.assertTrue(isinstance(found.connection(), Connection))
        self.assertEqual(found.id(), DATASET_ID)
        self.assertTrue(client._get_app_default_called)


class Test_implicit_behavior(unittest2.TestCase):

    def test__require_dataset_value_unset(self):
        import gcloud.datastore
        from gcloud.datastore import _implicit_environ
        from gcloud._testing import _Monkey

        with _Monkey(_implicit_environ, DATASET=None):
            with self.assertRaises(EnvironmentError):
                gcloud.datastore._require_dataset()

    def test__require_dataset_value_set(self):
        import gcloud.datastore
        from gcloud.datastore import _implicit_environ
        from gcloud._testing import _Monkey

        FAKE_DATASET = object()
        with _Monkey(_implicit_environ, DATASET=FAKE_DATASET):
            stored_dataset = gcloud.datastore._require_dataset()
        self.assertTrue(stored_dataset is FAKE_DATASET)

    def test__require_connection_value_unset(self):
        import gcloud.datastore
        from gcloud.datastore import _implicit_environ
        from gcloud._testing import _Monkey

        with _Monkey(_implicit_environ, CONNECTION=None):
            with self.assertRaises(EnvironmentError):
                gcloud.datastore._require_connection()

    def test__require_connection_value_set(self):
        import gcloud.datastore
        from gcloud.datastore import _implicit_environ
        from gcloud._testing import _Monkey

        FAKE_CONNECTION = object()
        with _Monkey(_implicit_environ, CONNECTION=FAKE_CONNECTION):
            stored_connection = gcloud.datastore._require_connection()
        self.assertTrue(stored_connection is FAKE_CONNECTION)

    def test_get_entities(self):
        import gcloud.datastore
        from gcloud.datastore import _implicit_environ
        from gcloud.datastore.test_entity import _Dataset
        from gcloud._testing import _Monkey

        CUSTOM_DATASET = _Dataset()
        DUMMY_KEYS = [object(), object()]
        DUMMY_VALS = [object(), object()]
        for key, val in zip(DUMMY_KEYS, DUMMY_VALS):
            CUSTOM_DATASET[key] = val

        with _Monkey(_implicit_environ, DATASET=CUSTOM_DATASET):
            result = gcloud.datastore.get_entities(DUMMY_KEYS)
        self.assertTrue(result == DUMMY_VALS)

    def test_allocate_ids(self):
        import gcloud.datastore
        from gcloud.datastore import _implicit_environ
        from gcloud.datastore.key import Key
        from gcloud.datastore.test_dataset import _Connection
        from gcloud.datastore.test_entity import _Dataset
        from gcloud._testing import _Monkey

        CUSTOM_DATASET = _Dataset()
        CUSTOM_CONNECTION = _Connection()
        NUM_IDS = 2
        with _Monkey(_implicit_environ, DATASET=CUSTOM_DATASET,
                     CONNECTION=CUSTOM_CONNECTION):
            INCOMPLETE_KEY = Key('KIND')
            result = gcloud.datastore.allocate_ids(INCOMPLETE_KEY, NUM_IDS)

        # Check the IDs returned.
        self.assertEqual([key.id for key in result], range(NUM_IDS))
