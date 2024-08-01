""" Test helper tools

Classes:

* :py:class:`FileSystemTestCase`: Tests that need a temporary directory
* :py:class:`StreamRecord`: Record a stream like sys.stdout

Decorators:

* :py:func:`record_stdout`: Record stdout in a context or decorator

"""

# Imports
import unittest
import tempfile
import pathlib

# Helper classes


class FileSystemTestCase(unittest.TestCase):
    """ Set up and tear down a temporary filesystem """

    def setUp(self):
        self._tempdir_obj = tempfile.TemporaryDirectory()
        self.tempdir = pathlib.Path(self._tempdir_obj.__enter__()).resolve()

    def tearDown(self):
        self.tempdir = None
        self._tempdir_obj.__exit__(None, None, None)
        self._tempdir_obj = None
