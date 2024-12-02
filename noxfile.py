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

import nox


SOURCE_FILES = ("noxfile.py", "tests/", "ecs_logging/")


def tests_impl(session):
    session.install(".[develop]")
    # Install `elastic-apm` from master branch
    session.install(
        "elastic-apm @ https://github.com/elastic/apm-agent-python/archive/master.zip"
    )
    session.run(
        "pytest",
        "--junitxml=junit-test.xml",
        "--cov=ecs_logging",
        *(session.posargs or ("tests/",)),
        env={"PYTHONWARNINGS": "always::DeprecationWarning"},
    )


@nox.session(python=["3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12"])
def test(session):
    tests_impl(session)


@nox.session()
def blacken(session):
    session.install("black")
    session.run("black", "--target-version=py36", *SOURCE_FILES)

    lint(session)


@nox.session
def lint(session):
    session.install("flake8", "black", "mypy")
    session.run("black", "--check", "--target-version=py36", *SOURCE_FILES)
    session.run("flake8", "--ignore=E501,W503", *SOURCE_FILES)
    session.run(
        "mypy",
        "--strict",
        "--show-error-codes",
        "ecs_logging/",
    )
