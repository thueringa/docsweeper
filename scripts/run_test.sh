#! /bin/bash

# Run the tests.
set -ev

echo $(pwd)
ls -la
cat pytest.ini
poetry run pytest --vcs "$VCS" -- src/tests
