### Releasing

Releases tags are signed so you need to have a PGP key set up, you can follow Github documentation on [creating a key](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key) and
on [telling git about it](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key). Alternatively you can sign with a SSH key, remember you have to upload your key
again even if you want to use the same key you are using for authorization.
Then make sure you have SSO figured out for the key you are using to push to github, see [Github documentation](https://docs.github.com/articles/authenticating-to-a-github-organization-with-saml-single-sign-on/).

If you have commit access, the process is as follows:

1. Update the version in `ecs_logging/__init__.py` according to the scale of the change. (major, minor or patch)
1. Update `CHANGELOG.md`.
1. Commit changes with message `update CHANGELOG and rev to vX.Y.Z`
   where `X.Y.Z` is the version in `ecs_logging/__init__.py`
1. Open a PR against `main` with these changes leaving the body empty
1. Once the PR is merged, fetch and checkout `upstream/main`
1. Tag the commit with `git tag -s X.Y.Z`, for example `git tag -s 2.2.0`.
   Copy the changelog for the release to the tag message, removing any leading `#`.
1. Push tag upstream with `git push upstream --tags` (and optionally to your own fork as well)
1. After tests pass, Github Actions will automatically build and push the new release to PyPI.
1. Edit and publish the [draft Github release](https://github.com/elastic/ecs-logging-python/releases).
   Substitute the generated changelog with one hand written into the body of the release.
