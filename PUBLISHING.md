# Publishing `abom-cli` to PyPI

`abom-cli` publishes to PyPI automatically when you push a version tag, using
**PyPI Trusted Publishing** (OIDC — no API tokens stored in the repo).

## One-time setup (you do this once on PyPI)

1. Create a PyPI account and verify your email.
2. Go to **PyPI → Your projects → Publishing** (or the project's *Manage → Publishing*
   once it exists) and add a **pending trusted publisher** with:
   - **PyPI project name:** `abom-cli`
   - **Owner:** `josephassiga`
   - **Repository name:** `abom`
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi`
3. In the GitHub repo, create an **Environment** named `pypi`
   (*Settings → Environments → New environment*). Optionally add required reviewers
   so a human approves each publish.

That's it — no secrets to manage.

## Cut a release

```bash
# bump the version in cli/pyproject.toml first (e.g. 0.1.0 -> 0.1.1)
git commit -am "release: v0.1.1"
git tag v0.1.1
git push origin main --tags
```

The [`release.yml`](.github/workflows/release.yml) workflow builds the sdist +
wheel, runs `twine check`, and publishes to PyPI. Within a minute or two:

```bash
pip install abom-cli
abom scan .
```

## Test on TestPyPI first (optional)

Add a second trusted publisher on https://test.pypi.org with the same settings,
then in `release.yml` set `repository-url: https://test.pypi.org/legacy/` on the
publish step for a dry run before going to real PyPI.

## Versioning

The version lives in [`cli/pyproject.toml`](cli/pyproject.toml). Update
[`CHANGELOG.md`](CHANGELOG.md) for each release. The project follows SemVer from 1.0.
