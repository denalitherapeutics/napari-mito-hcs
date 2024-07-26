""" Test helper tools

Classes:

* :py:class:`FileSystemTestCase`: Tests that need a temporary directory
* :py:class:`StreamRecord`: Record a stream like sys.stdout

Decorators:

* :py:func:`record_stdout`: Record stdout in a context or decorator

"""

# Imports
import sys
import unittest
import tempfile
import pathlib
import contextlib

# 3rd party
import numpy as np

import matplotlib.pyplot as plt

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


class StreamRecord(object):
    """ Record stream objects like sys.stdout """

    def __init__(self):
        self.lines = []

    def write(self, line):
        self.lines.append(line)


# Helper functions


def compare_images(image1: np.ndarray, image2: np.ndarray,
                   ax1_title: str = '',
                   ax2_title: str = '',
                   fig_title: str = ''):
    """ Plot two images to compare side-by-side """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), sharex=True, sharey=True)
    ax1.imshow(image1)
    ax1.set_title(ax1_title)
    ax2.imshow(image2)
    ax2.set_title(ax2_title)
    fig.suptitle(fig_title)
    plt.show()


@contextlib.contextmanager
def record_stdout():
    """ Record the standard output to inspect later """

    old_stdout = sys.stdout

    try:
        sys.stdout = StreamRecord()
        yield sys.stdout
    finally:
        sys.stdout = old_stdout
