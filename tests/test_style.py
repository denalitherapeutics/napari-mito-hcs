#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Style tests for all modules """

# Standard Lib
import unittest
import pathlib
import os
import re
from collections.abc import Callable

# 3rd-party
import pycodestyle

from pyflakes.api import checkPath as pyflakes_checkPath

# Constants

PARENTDIR = str(pathlib.Path(__file__).resolve().parent.parent)

reMETHOD = re.compile(r'[^a-zA-Z0-9\_]')
reMETATEST = re.compile(r'^metatest_.*', re.IGNORECASE)

# These directories should be skipped completely
SKIP_DIRS = ['build', 'dist', 'venv', 'lib', 'bin', 'include', 'etc', 'man']

# Tests


class MetaTestStyle(type):
    """ Add a method to the class for each entry point """

    def __new__(cls, name, bases, dct):

        if dct.get('__abstract__', False):
            return super(MetaTestStyle, cls).__new__(cls, name, bases, dct)

        targets = cls.find_targets(PARENTDIR)
        testcases = cls.find_test_cases(dct)

        if len(targets) < 1:
            msg = 'No target python files found in: {}'
            msg = msg.format(PARENTDIR)
            assert False, msg

        if len(testcases) < 1:
            msg = 'No test cases found for class: {}'
            msg = msg.format(name)
            assert False, msg

        cls_blacklist = dct.get('BLACKLIST', {})

        # Load up each test case with each path
        for testcase in testcases:
            blacklist = cls_blacklist.get(testcase, set())
            dct = cls.add_test_case(dct, testcase, targets, blacklist)

        return super(MetaTestStyle, cls).__new__(cls, name, bases, dct)

    @classmethod
    def find_targets(cls, targetroot):
        """ Find all the python files under a root location """

        if not os.path.isdir(targetroot):
            return []

        targets = []
        for root, dirs, files in os.walk(targetroot):

            for skip_dir in SKIP_DIRS:
                skip_dir = os.path.join(targetroot, skip_dir)
                if not os.path.exists(skip_dir):
                    continue

                if os.path.samefile(root, skip_dir):
                    dirs[:] = []
                    files[:] = []
                    break

            dirs[:] = [d for d in dirs if not d.startswith('.')]

            files = (f1 for f1 in files
                     if not f1.startswith('.') and f1.endswith('.py'))

            fullfiles = (os.path.join(root, f2) for f2 in files)

            targets.extend((os.path.relpath(f3, targetroot), f3)
                           for f3 in fullfiles)

        return sorted(targets)

    @classmethod
    def find_test_cases(cls, dct):
        """ Find all the methods on the class that match """

        testcases = []
        for key in dct:
            if reMETATEST.match(key):
                testcases.append(key)
        return testcases

    @classmethod
    def add_test_case(cls, dct, testcase, targets, blacklist):
        """ Add a single test case for each path in targets """

        fxn = dct[testcase]

        err = "Expected {} to be a callable method"
        err = err.format(testcase)
        assert isinstance(fxn, Callable), err

        for relpath, path in targets:

            key = reMETHOD.sub('_', relpath)
            fxn_name = 'test_{}_{}'.format(key, testcase)

            msg = 'Already have a test function: {}'
            msg = msg.format(fxn_name)
            assert fxn_name not in dct, msg

            lfxn = (lambda self, fxn=fxn, path=path: fxn(self, path))

            if relpath in blacklist:
                msg = "{} was blacklisted for test {}"
                msg = msg.format(relpath, testcase)
                blfxn = unittest.skip(msg)

                blfxn = blfxn(lfxn)
            else:
                blfxn = lfxn

            bldoc = fxn.__doc__.format(relpath=relpath,
                                       path=path)
            blfxn.__name__ = fxn_name  # nose looks for this ><
            blfxn.__doc__ = bldoc  # Docstring for nosetests -v
            dct[fxn_name] = blfxn  # unittest looks for this ><

        return dct


# Metaclass magic that is python 2 and 3 compatible
_TestStyle = MetaTestStyle('TestStyle',
                           (unittest.TestCase, ),
                           {'__abstract__': True})


class TestStyle(_TestStyle):
    """ Make sure each script is well-formed python """

    BLACKLIST = {}

    def metatest_pyflakes(self, path):
        """ Pyflakes conformance for {relpath} """

        total_errors = pyflakes_checkPath(path)

        msg = f'Found {total_errors} Pyflakes violations in: {path}'
        self.assertEqual(total_errors, 0, msg=msg)

    def metatest_pycodestyle(self, path):
        """ Code style conformance for {relpath} """

        # We ignore these rules, because they're too dumb to follow
        # E501 - max line length
        # E265 - block comments
        # E402 - module level imports
        ignore_codes = ('E265', 'E501', 'E402')

        pycode_guide = pycodestyle.StyleGuide()

        pycode_guide.options.ignore += ignore_codes
        # pycodestyle.options.max_line_length = 100
        result = pycode_guide.check_files([path])

        total_errors = result.total_errors

        err = f'Found {total_errors} code style violations in: {path}'
        self.assertEqual(total_errors, 0, err)


if __name__ == '__main__':
    unittest.main()
