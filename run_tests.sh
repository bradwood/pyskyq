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
echo TODO: 'Implement pydocstyle here and in CI!'
