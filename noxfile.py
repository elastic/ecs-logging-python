import os
import shutil

import nox


SOURCE_FILES = ("noxfile.py", "tests/", "docs/", "ecs_logging/")


def tests_impl(session):
    session.install(".[develop]")
    session.run(
        "pytest",
        *(session.posargs or ("tests/",)),
        env={"PYTHONWARNINGS": "always::DeprecationWarning"}
    )


@nox.session(python=["2.7", "3.5", "3.6", "3.7", "3.8"])
def test(session):
    tests_impl(session)


@nox.session()
def blacken(session):
    """Run black code formatter."""
    session.install("black")
    session.run("black", "--target-version=py27", *SOURCE_FILES)

    lint(session)


@nox.session
def lint(session):
    session.install("flake8", "black")
    session.run("black", "--check", "--target-version=py27", *SOURCE_FILES)
    session.run("flake8", *SOURCE_FILES)


@nox.session
def docs(session):
    session.install("sphinx")
    session.install(".")

    session.chdir("docs")
    if os.path.exists("_build"):
        shutil.rmtree("_build")
    session.run("sphinx-build", "-W", ".", "_build/html")
