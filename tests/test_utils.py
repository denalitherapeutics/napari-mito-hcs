""" Test the example loader classes """

# Imports
import unittest

# Our own imports
from napari_mito_hcs import utils

# Tests


class TestLoadsDemoImages(unittest.TestCase):

    def test_load_wt_images(self):

        res = utils.load_example_images('wt')
        assert set(res.keys()) == {'cell', 'mito', 'nucl'}

        for val in res.values():
            assert val.shape == (1080, 1080)

    def test_load_ko_images(self):

        res = utils.load_example_images('ko')
        assert set(res.keys()) == {'cell', 'mito', 'nucl'}

        for val in res.values():
            assert val.shape == (1080, 1080)

    def test_load_wt_labels(self):

        res = utils.load_example_labels('wt')
        assert set(res.keys()) == {'cell', 'mito', 'nucl'}

        for val in res.values():
            assert val.shape == (1080, 1080)

    def test_load_ko_labels(self):

        res = utils.load_example_labels('ko')
        assert set(res.keys()) == {'cell', 'mito', 'nucl'}

        for val in res.values():
            assert val.shape == (1080, 1080)

    def test_load_wt_features(self):

        res = utils.load_example_features('wt')
        assert set(res.keys()) == {'spot', 'hole', 'ridge', 'valley', 'saddle'}

        for val in res.values():
            assert val.shape == (1080, 1080)

    def test_load_ko_features(self):

        res = utils.load_example_features('ko')
        assert set(res.keys()) == {'spot', 'hole', 'ridge', 'valley', 'saddle'}

        for val in res.values():
            assert val.shape == (1080, 1080)
