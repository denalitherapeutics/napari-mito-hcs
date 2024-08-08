""" Shape Index Feature Pipeline

Example: Extract all the features from an image:

.. code-block:: python

    pipeline = ShapeIndexPipeline(features=['spot', 'hole', 'ridge', 'valley'])
    si_features = pipeline(intensity_image)

    # Features are returned in order
    spot_feature = si_features[:, :, 0]
    hole_feature = si_features[:, :, 1]
    ridge_feature = si_features[:, :, 2]
    valley_feature = si_features[:, :, 3]

Classes:

* :py:class:`ShapeIndexPipeline`: Pipeline for extracting shape index features

"""

# Imports
from typing import Optional, List, Union

# 3rd party
import numpy as np

from skimage import restoration, feature

import scipy.ndimage as ndi

# our own imports
from .config import Configurable

# Classes


class ShapeIndexPipeline(Configurable):
    """ Extract shape index features

    :param list[str] features:
        The list of shape index features to extract
    :param int parabola_height:
        If >0, height (in px) of the parabolic filter to use for background subtraction
    :param float intensity_smoothing:
        If >0, smooth the intensity image with gaussian kernel before extracting features
    """

    def __init__(self,
                 features: Optional[Union[List[str], str]] = None,
                 parabola_height: int = 50,
                 intensity_smoothing: float = 0.75):

        if features is None:
            features = self.list_available_features()
        elif isinstance(features, str):
            features = [features]
        self.features = [feature_name for feature_name in features]

        self.parabola_height = parabola_height
        self.intensity_smoothing = intensity_smoothing

    @staticmethod
    def list_available_features() -> List[str]:
        """ Get a list of all the features we **could** calculate

        :returns:
            A list of feature names that can be calculated
        """
        return ['spot', 'hole', 'ridge', 'valley', 'saddle']

    def subtract_background_parabolic(self, intensity_image: np.ndarray) -> np.ndarray:
        """ Apply a parabolic background correction

        Uses a 2D sliding parabola filter with a height of ``self.parabola_height**2`` at (0, 0) which
        slopes down towards 0 in both x and y.

        If ``self.parabola_height`` is None or < 0, the original image is returned.

        :param ndarray intensity_image:
            The 2D (n x m) intensity image to subtract the background from
        :returns:
            The 2D (n x m) image after background subtraction. Values below the background are set to 0
        """

        if self.parabola_height is None or self.parabola_height <= 0:
            return intensity_image

        halfwidth = int(np.ceil(self.parabola_height))

        x = np.linspace(-halfwidth, halfwidth, 2*halfwidth+1)
        xx, yy = np.meshgrid(x, x)
        kernel = self.parabola_height**2 - (xx**2 + yy**2)
        kernel[kernel < 0] = np.inf

        # Apply the filter with our parabolic kernel instead of the typical ball kernel
        background_image = restoration.rolling_ball(intensity_image, kernel=kernel)
        intensity_image = intensity_image - background_image
        intensity_image[intensity_image < 0] = 0
        return intensity_image

    def __call__(self, intensity_image: np.ndarray) -> np.ndarray:
        """ Extract shape index features

        :param ndarray intensity_image:
            The 2D (n x m) intensity image to extract features from
        :returns:
            A 3D (n x m x c) feature image with features in the same order as ``self.features``
        """
        intensity_image = intensity_image.astype(np.float32)

        intensity_image = self.subtract_background_parabolic(intensity_image)

        # Smooth the intensity image to help with numeric stability
        if self.intensity_smoothing is None or self.intensity_smoothing < 1e-2:
            smooth_image = intensity_image.copy()
        else:
            smooth_image = ndi.gaussian_filter(intensity_image, self.intensity_smoothing)

        # Calculate first and second derivatives of the smoothed intensity image
        g_x, g_y = np.gradient(smooth_image)

        h_xx = np.gradient(g_x, axis=0)
        h_xy = np.gradient(g_x, axis=1)
        h_yy = np.gradient(g_y, axis=1)

        # Calculate principal curvatures
        h_uu, h_vv = feature.hessian_matrix_eigvals([h_xx, h_xy, h_yy])

        # Shape index - convert the principal curvature to a score between -1 and 1
        shape_index = (2 / np.pi) * np.arctan2(h_vv + h_uu, h_vv - h_uu)  # scikit-image uses arctan but this causes infs/nans
        shape_index[shape_index > 1] = shape_index[shape_index > 1] - 2  # reflect >180 degrees
        shape_index[shape_index < -1] = shape_index[shape_index < -1] + 2  # reflect <-180 degrees

        # Calculate the shape index images
        norm_image = (smooth_image + 1e-2)  # Add an epsilon to prevent divide by zero
        feature_images = []
        for feature_name in self.features:
            # Feature masks are similar to categories from Koenderink and van Doorn (1992) but have width 1/2 instead of 1/4:
            # Ex: cap (7/8, 1), dome (5/8, 7/8), and part of ridge (3/8, 5/8) get merged into "spot"
            # Ex: part of dome (5/8, 7/8), ridge (3/8, 5/8) and part of saddle ridge (1/8, 3/8) get merged into "ridge"
            if feature_name == 'spot':
                feature_mask = shape_index > 0.5
                feature_image = np.abs(h_uu)
            elif feature_name == 'hole':
                feature_mask = shape_index < -0.5
                feature_image = np.abs(h_vv)
            elif feature_name == 'ridge':
                feature_mask = (shape_index > 0.25) & (shape_index < 0.75)
                feature_image = np.abs(h_vv)
            elif feature_name == 'valley':
                feature_mask = (shape_index > -0.75) & (shape_index < -0.25)
                feature_image = np.abs(h_uu)
            elif feature_name == 'saddle':
                feature_mask = (shape_index > -0.25) & (shape_index < 0.25)
                feature_image = np.abs(h_vv)
            else:
                raise ValueError(f'Unknown feature: "{feature_name}"')

            # Shape images are normalized by the smoothed intensity image and zeroed outside the mask
            feature_image = feature_image / norm_image
            feature_image[~feature_mask] = 0
            feature_images.append(feature_image)
        return np.stack(feature_images, axis=2)
