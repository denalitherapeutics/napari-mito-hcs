""" Tests for the feature module """

# Imports
import unittest

# 3rd party
import numpy as np

# Our own imports
from napari_mito_hcs import feature, utils

# Tests


class TestShapeIndexPipeline(unittest.TestCase):

    # Unit tests

    def test_basic_spot_feature(self):

        # Make some wave shaped images
        x = np.linspace(0, 10*np.pi, 100)
        xx, yy = np.meshgrid(x, x)

        zz = np.cos(xx) + np.sin(yy)

        pipeline = feature.ShapeIndexPipeline(
            features='spot',
            intensity_smoothing=0.0,
            parabola_height=0,
        )
        feature_image = pipeline(zz)
        assert feature_image.shape == (100, 100, 1)

    def test_basic_all_features(self):

        # Make some wave shaped images
        x = np.linspace(0, 10*np.pi, 100)
        xx, yy = np.meshgrid(x, x)

        zz = np.cos(xx) + np.sin(yy)

        pipeline = feature.ShapeIndexPipeline(
            features=None,
            intensity_smoothing=0.0,
            parabola_height=0,
        )
        feature_image = pipeline(zz)
        assert feature_image.shape == (100, 100, 5)

    # Integration tests

    def test_shape_index_features_match(self):

        for example in ['wt', 'ko']:
            cell_image = utils.load_example_images(example)['mito']

            pipeline = feature.ShapeIndexPipeline.load_default('shape_index')

            res = pipeline(cell_image)
            exp = utils.load_example_features(example)

            for i, feature_name in enumerate(pipeline.features):
                with self.subTest(example=example, feature_name=feature_name):
                    np.testing.assert_allclose(res[:, :, i], exp[feature_name], atol=1e-2, rtol=1e-2)
