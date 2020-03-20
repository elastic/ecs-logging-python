#!/usr/bin/env bash
set -e

VERSION=${1:?Please specify the python version}

python -m pip install -U nox
nox -s test-"${VERSION}"