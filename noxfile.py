import nox


SOURCE_FILES = ("noxfile.py", "tests/", "ecs_logging/")


def tests_impl(session):
    session.install(".[develop]")
    session.run(
        "pytest",
        "--junitxml=junit-test.xml",
        "--cov=ecs_logging",
        *(session.posargs or ("tests/",)),
        env={"PYTHONWARNINGS": "always::DeprecationWarning"}
    )


@nox.session(python=["2.7", "3.5", "3.6", "3.7", "3.8"])
def test(session):
    tests_impl(session)


@nox.session()
def blacken(session):
    session.install("black")
    session.run("black", "--target-version=py27", *SOURCE_FILES)

    lint(session)


@nox.session
def lint(session):
    session.install("flake8", "black", "mypy")
    session.run("black", "--check", "--target-version=py27", *SOURCE_FILES)
    session.run("flake8", "--ignore=E501,W503", *SOURCE_FILES)
    session.run("mypy", "--strict", "ecs_logging/")
