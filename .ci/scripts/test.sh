#!/usr/bin/env bash
set -e

VERSION=${1:?Please specify the python version}

## When running in a docker container in the CI then it's required to set the location
## for the tools to be installed.
export PATH=${HOME}/.local/bin:${PATH}

python -m pip install -U nox
nox -s test-"${VERSION}"