import datetime
import json
import os

import pytest


class ValidationError(Exception):
    pass


@pytest.fixture
def spec_validator():
    with open(
        os.path.join(os.path.dirname(__file__), "resources", "spec.json"), "r"
    ) as fh:
        spec = json.load(fh)

    def validator(data_json):
        """
        Throws a ValidationError if anything doesn't match the spec.

        Returns the original json (pass-through)
        """
        fields = spec["fields"]
        data = json.loads(data_json)
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
                    raise ValidationError("Missing required key {}".format(k))
            if k in data:
                if v["type"] == "string" and not (
                    isinstance(data[k], str) or isinstance(data[k], basestring)
                ):
                    raise ValidationError(
                        "Value {0} for key {1} should be string, is {2}".format(
                            data[k], k, type(data[k])
                        )
                    )
                if v["type"] == "datetime":
                    try:
                        datetime.datetime.strptime(data[k], "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        raise ValidationError(
                            "Value {0} for key {1} doesn't parse as an ISO datetime".format(
                                data[k], k
                            )
                        )
            if v.get("index"):
                index = v.get("index")
                key = json.loads(
                    data_json.split(",")[index].split(":")[0].strip().lstrip("{")
                )
                if key != k:
                    raise ValidationError(
                        "Key {0} is not at index {1}".format(k, index)
                    )

        return data_json

    return validator
