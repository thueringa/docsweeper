#! /bin/bash

# Run the tests.
set -ev

echo $(pwd)
ls -la
cat pytest.ini
poetry run pytest --basetemp=$HOME/tmp --vcs "$VCS" -- src/tests
