""" Tests for the feature module """

# Imports
import unittest

# 3rd party
import numpy as np

import scipy.ndimage as ndi

# Our own imports
from napari_mito_hcs import example_utils, feature, data

# Tests


class TestShapeIndexPipeline(unittest.TestCase):

    # Helper functions

    def make_wave_image(self,
                        num_samples: int = 100,
                        num_periods: float = 5.0,
                        phase: float = 0.0) -> np.ndarray:
        """ Make a wave shaped image

        :param int num_samples:
            How many pixels to sample along the x and y axis
        :param float num_periods:
            How many periods of the sine wave should we have in the image
        :param float phase:
            Phase offset to move the peaks/troughs of the wave
        :returns:
            An image that is a mix of sine and cosine waves with shape (num_samples, num_samples)
        """
        # Make some wave shaped images
        x = np.linspace(0, num_periods*2*np.pi, num_samples) + phase
        xx, yy = np.meshgrid(x, x)
        zz = np.cos(xx) + np.sin(yy)
        return zz * 255.0

    # Unit tests

    def test_basic_spot_feature(self):

        image = self.make_wave_image(num_samples=250, num_periods=4, phase=np.pi/4)

        pipeline = feature.ShapeIndexPipeline(
            features='spot',
            intensity_smoothing=0.0,
            parabola_height=0,
        )
        feature_image = pipeline(image)
        assert feature_image.shape == (250, 250, 1)

        # The spot filter converts the wave image to evenly spaced triangular prisms
        _, num_labels = ndi.label(feature_image[:, :, 0] > 1e-5)

        # Should have one more than the number of periods in each direction
        assert num_labels == 25

    def test_basic_ridge_feature(self):

        image = self.make_wave_image(num_samples=250, num_periods=4, phase=np.pi/4)

        pipeline = feature.ShapeIndexPipeline(
            features='ridge',
            intensity_smoothing=0.0,
            parabola_height=0,
        )
        feature_image = pipeline(image)
        assert feature_image.shape == (250, 250, 1)

        # The ridge filter converts the wave image to ellipses arranged in a sqaure pattern
        _, num_labels = ndi.label(feature_image[:, :, 0] > 1e-2)

        # 25 squares x 4 ellipses per-square but the corners are cut off on all 4 sides
        assert num_labels == 80

    def test_basic_all_features(self):

        # Make some wave shaped images
        image = self.make_wave_image(num_samples=100, num_periods=5)

        pipeline = feature.ShapeIndexPipeline(
            features=None,
            intensity_smoothing=0.0,
            parabola_height=0,
        )
        feature_image = pipeline(image)
        assert feature_image.shape == (100, 100, 5)

    def test_subtract_background_parabolic_off(self):

        image = self.make_wave_image(num_samples=100, num_periods=5)

        pipeline = feature.ShapeIndexPipeline(
            features=None,
            intensity_smoothing=0.0,
            parabola_height=0,
        )
        exp_image = image.copy()
        res_image = pipeline.subtract_background_parabolic(image)

        np.testing.assert_allclose(res_image, exp_image)

    def test_subtract_background_parabolic_on(self):

        # Absolute value because background subtraction is weird about negative values
        image = np.abs(self.make_wave_image(num_samples=100, num_periods=5))

        pipeline = feature.ShapeIndexPipeline(
            features=None,
            intensity_smoothing=0.0,
            parabola_height=5,
        )
        exp_image = image.copy()
        res_image1 = pipeline.subtract_background_parabolic(image)

        # Subtracting background should reduce signal vs the original image
        np.testing.assert_array_less(res_image1, exp_image)

        pipeline = feature.ShapeIndexPipeline(
            features=None,
            intensity_smoothing=0.0,
            parabola_height=20,
        )
        exp_image = image.copy()
        res_image2 = pipeline.subtract_background_parabolic(image)

        # Wider parabola -> less signal loss
        np.testing.assert_array_less(res_image2, exp_image)
        assert np.all(res_image1 <= res_image2)

    # Integration tests

    def test_shape_index_features_match(self):

        for example in data.EXAMPLE_TYPES:
            cell_image = example_utils.load_example_images(example)['mito']

            pipeline = feature.ShapeIndexPipeline.load_default('shape_index')

            res = pipeline(cell_image)
            exp = example_utils.load_example_features(example)

            for i, feature_name in enumerate(pipeline.features):
                with self.subTest(example=example, feature_name=feature_name):
                    np.testing.assert_allclose(res[:, :, i], exp[feature_name], atol=1e-2, rtol=1e-2)
