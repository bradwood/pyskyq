#!/usr/bin/env bash
echo ---- pytest ----
echo
python setup.py test
echo
echo ---- mypy ----
echo
mypy src --quick-and-dirty --ignore-missing-imports
echo
echo ---- pylint ----
echo
pylint src
echo
echo ---- pydocstyle ----
echo
pydocstyle src
echo ---- checking docs and metadata ----
python setup.py check --restructuredtext --strict  # make sure README.rst parses okay.
python setup.py check --metadata --strict # check metadata for correctness.
