# pylint: skip-file

import contextlib
import os
import shutil
import tempfile

# Shamelessly stolen from the excellent Click library:
# See https://github.com/pallets/click/blob/master/click/testing.py

@contextlib.contextmanager
def isolated_filesystem():
    """A context manager that creates a temporary folder and changes
    the current working directory to it for isolated filesystem tests.
    """
    cwd = os.getcwd()
    t = tempfile.mkdtemp()
    os.chdir(t)
    try:
        yield t
    finally:
        os.chdir(cwd)
        try:
            shutil.rmtree(t)
        except (OSError, IOError):
            pass
