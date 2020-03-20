#!/usr/bin/env bash
set -e

python -m pip install -U nox
nox -e lint