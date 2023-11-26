# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import collections
import datetime
import json
import logging
import os

import elasticapm
import pytest


class ValidationError(Exception):
    pass


@pytest.fixture
def spec_validator():
    with open(os.path.join(os.path.dirname(__file__), "resources", "spec.json")) as fh:
        spec = json.load(fh)

    def validator(data_json):
        """
        Throws a ValidationError if anything doesn't match the spec.

        Returns the original json (pass-through)
        """
        fields = spec["fields"]
        data = json.loads(data_json, object_pairs_hook=collections.OrderedDict)
        for k, v in fields.items():
            if v.get("required"):
                found = False
                if k in data:
                    found = True
                elif "." in k:
                    # Dotted keys could be nested, like ecs.version
                    subkeys = k.split(".")
                    subval = data
                    for subkey in subkeys:
                        subval = subval.get(subkey, {})
                    if subval:
                        found = True
                if not found:
                    raise ValidationError(f"Missing required key {k}")
            if k in data:
                if v["type"] == "string" and not isinstance(data[k], str):
                    raise ValidationError(
                        "Value {} for key {} should be string, is {}".format(
                            data[k], k, type(data[k])
                        )
                    )
                if v["type"] == "datetime":
                    try:
                        datetime.datetime.strptime(data[k], "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        raise ValidationError(
                            "Value {} for key {} doesn't parse as an ISO datetime".format(
                                data[k], k
                            )
                        )
            if v.get("index") and list(data.keys())[v.get("index")] != k:
                raise ValidationError(f"Key {k} is not at index {v.get('index')}")

        return data_json

    return validator


@pytest.fixture
def apm():
    record_factory = logging.getLogRecordFactory()
    apm = elasticapm.Client(
        {"SERVICE_NAME": "apm-service", "ENVIRONMENT": "dev", "DISABLE_SEND": True}
    )
    yield apm
    apm.close()
    logging.setLogRecordFactory(record_factory)
