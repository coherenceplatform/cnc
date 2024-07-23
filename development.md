Contributions via PR to this repo are welcome. Please for the repo, work on your feature or change using the guide below, and then make a PR against this repo. The team will review the PR and work with you to get it merged. Thanks!

# install pipx
[pipx installation instructions](https://pipx.pypa.io/stable/installation)

e.g. for macOS
```bash
brew install pipx
pipx ensurepath
```

# install poetry
[poetry](https://python-poetry.org/docs/)

e.g.
```bash
pipx install poetry
```

# install dev dependencies
```bash
poetry install --with dev
```
Poetry will also install a script so the cli
can be run using `cnc` as if there was a binary installed.


# start a shell in the python virtual env
```bash
# starts a login shell in the virtual env created by poetry
# pre-requisite for the following commands (python shell, cli, etc.)
poetry shell
```

# running the tests
Run this in the `src` dir after running `poetry shell` as per above.

```bash
pytest
```

You can also run something like this to run one class (no need to qualify with path):
```pytest -k EnvironmentCollectionExistingDBTestCase -v```

# start an interactive python shell (ipython)
You can do this from anywhere once you have activated poetry shell

```bash
cnc shell start
```
e.g.:
- start in your `cnc` repo
- `poetry shell`
- `cd ../MY_SITE_DIR`
- `cnc shell start`


# running the cli
```bash
cnc --help
```

# dependencies

## Python
developed using python 🐍 >= 3.9
(check yours with `python --version`)

There's a codespace set up in the repo where you just run `poetry shell` and you're all set to work, that's the easiest place to be.


# Releasing a new version

## Setup PyPI creds

e.g. populate ~/.pypirc

## Steps

- `python3 -m pip install --upgrade build`
- `python3 -m build`
- `python3 -m twine upload dist/*`