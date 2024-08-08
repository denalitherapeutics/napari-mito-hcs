""" Utilities for accessing examples in the repository

Functions:

* :py:func:`load_example_images`: Load example intensity images
* :py:func:`load_example_labels`: Load example segmentation images
* :py:func:`load_example_features`: Load example feature images

"""

# Imports
from importlib import resources
from typing import Dict, List, Optional

# 3rd party
import numpy as np

import tifffile

# Our own imports
from . import data

# Helpers


def _load_from_package(example_dir: resources.abc.Traversable,
                       example_paths: List[str],
                       scale_factors: Optional[Dict[str, float]] = None) -> Dict[str, np.ndarray]:
    """ Generic code to load a set of files from the package resources

    :param Anchor example_dir:
        The resources.Anchor pointing to the subdirectory where the images are
    :param list[str] example_paths:
        The list of ['cell_image.tif', 'mito_image.tif', ...] to load from the packge resources
    :param dict[str, float] scale_factors:
        If not None, a dictionary of scale factors to convert integer tiff images back into float images
    :returns:
        A dictionary of {name: data} keys where name is the image prefix up to the first '_' and
        data is the numpy array corresponding to that data
    """
    if scale_factors is None:
        scale_factors = {}

    example_images = {}
    for example_path in example_paths:
        prefix = example_path.split('_', 1)[0]
        example_file = example_dir / example_path
        with example_file.open('rb') as fp:
            example_data = tifffile.imread(fp)
        # If the images were packed, unpack them to get the ~original float values
        scale_factor = scale_factors.get(example_path)
        if scale_factor is not None:
            example_data = example_data.astype(np.float32)
            example_data = example_data / scale_factor
        example_images[prefix] = example_data
    return example_images

# Functions


def load_example_images(image_type: str = 'wt') -> Dict[str, np.ndarray]:
    """ Load example intensity images

    :param str image_type:
        One of 'wt' or 'ko', which of the example image sets to load
    :returns:
        A dictionary with keys 'cell', 'mito', 'nucl' corresponding to the
        CellMask, TOMM20, and DAPI stained images
    """
    example_paths = ['cell_image.tif', 'mito_image.tif', 'nucl_image.tif']
    example_dir = resources.files(data) / image_type
    return _load_from_package(example_dir, example_paths)


def load_example_labels(image_type: str = 'wt') -> Dict[str, np.ndarray]:
    """ Load example segmentation images

    :param str image_type:
        One of 'wt' or 'ko', which of the example image sets to load
    :returns:
        A dictionary with keys 'cell', 'mito', 'nucl' corresponding to the
        segmented cells, segmented mitochondria, and segmented nuclei
    """
    example_paths = ['cell_labels.tif', 'mito_labels.tif', 'nucl_labels.tif']
    example_dir = resources.files(data) / image_type
    return _load_from_package(example_dir, example_paths)


def load_example_features(image_type: str = 'wt') -> Dict[str, np.ndarray]:
    """ Load example segmentation images

    :param str image_type:
        One of 'wt' or 'ko', which of the example image sets to load
    :returns:
        A dictionary with keys 'spot', 'hole', 'ridge', 'valley', 'saddle' corresponding
        to the features extracted from the mitochondria image
    """
    example_paths = ['spot_feature.tif', 'hole_feature.tif', 'ridge_feature.tif', 'valley_feature.tif', 'saddle_feature.tif']

    # Empirically determined factors to pack the feature images into 16-bits
    scale_factors = {
        'spot_feature.tif': 2500,
        'hole_feature.tif': 900,
        'ridge_feature.tif': 1000,
        'valley_feature.tif': 250,
        'saddle_feature.tif': 1000,
    }
    example_dir = resources.files(data) / image_type
    return _load_from_package(example_dir, example_paths, scale_factors=scale_factors)
