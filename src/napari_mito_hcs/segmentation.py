""" Tools to segment cells, nuclei, and mitochondria in high content images

Example: Segment nuclei from a DAPI-stained image

.. code-block:: python

    pipeline = SegmentationPipeline.load_default('nuclei')
    nuclei_labels = pipeline(nuclei_image)

Given a nuclei segmentation, segment cells from a CellMask-stained image

.. code-block:: python

    pipeline = SegmentationPipeline.load_default('cells')
    cell_labels = pipeline(cell_image, nuclei_labels=nuclei_labels)

Given the nuclei and cell segmentations, extract mitochondria from a TOMM20-stained image

.. code-block:: python

    pipeline = SegmentationPipeline.load_default('mitochondria')
    mito_labels = pipeline(mito_image, cell_labels=cell_labels, nuclei_labels=nuclei_labels)

Classes:

* :py:class:`SegmentationPipeline`: Main class containing the segmentation algorithms

"""

# Imports
from typing import Optional

# 3rd party
import numpy as np

import scipy.ndimage as ndi

from skimage import segmentation, filters, morphology, feature

# Our own imports
from .config import Configurable

# Classes


class SegmentationPipeline(Configurable):
    """ Multi-stage segmentation pipeline to extract cell/nuclei/mitochondria masks

    :param float intensity_smoothing:
        Blur the image with a gaussian filter before thresholding (or <= 0.0 for no smoothing)
    :param float threshold:
        Threshold the image at this intensity to separate foreground and background
        (if None or < 0, the threshold is calculated by Otsu's method)
    :param int smallest_object:
        Size of the smallest foreground area to remove (in px)
    :param int largest_hole:
        Size of the largest background area to fill in (in px)
    :param int binary_smoothing:
        Smooth the final binary mask using this many steps of dilation followed by this many steps of erosion (in px)
    :param str algorithm:
        Which segmentation algorithm to use, one of 'nuclei', 'cells', 'mitochondria'.
        To define a new algorithm, create a method called ``segment_$algorithm`` on this class
    """

    def __init__(self,
                 intensity_smoothing: float = 0.0,
                 threshold: Optional[float] = None,
                 smallest_object: int = 0,
                 largest_hole: int = 0,
                 binary_smoothing: int = 0,
                 algorithm: str = 'nuclei'):
        self.intensity_smoothing = intensity_smoothing
        self.threshold = threshold
        self.smallest_object = smallest_object
        self.largest_hole = largest_hole
        self.binary_smoothing = binary_smoothing

        self.algorithm = algorithm

        self._tol = 1e-5

    def __call__(self,
                 intensity_image: np.ndarray,
                 cell_labels: Optional[np.ndarray] = None,
                 nuclei_labels: Optional[np.ndarray] = None) -> np.ndarray:
        """ Threshold the image with the given parameters

        :param ndarray intensity_image:
            The intensity image to segment
        :param ndarray cell_labels:
            If not None, constrain the segmentation with the provided cell label image
        :param ndarray nuclei_labels:
            If not None, constrain the segmentation with the provided nuclei label image
        :returns:
            A label image where 0 corresponds to background, and values >0 correspond to individual objects
        """

        # Smooth the raw intensity image
        if self.intensity_smoothing > self._tol:
            intensity_image = ndi.gaussian_filter(intensity_image, (self.intensity_smoothing, self.intensity_smoothing))

        # Binary threshold
        if self.threshold is None:
            self.threshold = filters.threshold_otsu(intensity_image)
        intensity_mask = intensity_image > self.threshold

        # Filter holes and small objects and smooth the mask
        if self.binary_smoothing > 0:
            intensity_mask = morphology.isotropic_dilation(intensity_mask, self.binary_smoothing)
        if self.largest_hole > 0:
            intensity_mask = morphology.remove_small_holes(intensity_mask, self.largest_hole)
        if self.binary_smoothing > 0:
            intensity_mask = morphology.isotropic_erosion(intensity_mask, self.binary_smoothing)
        if self.smallest_object > 0:
            intensity_mask = morphology.remove_small_objects(intensity_mask, self.smallest_object)

        # Select the segmentation algorithm by name
        try:
            segmentation_func = getattr(self, f'segment_{self.algorithm}')
        except AttributeError:
            raise AttributeError(f'No segmentation method defined for "segment_{self.algorithm}"')
        return segmentation_func(intensity_mask, cell_labels=cell_labels, nuclei_labels=nuclei_labels)

    # Segmentation methods

    def segment_nuclei(self,
                       intensity_mask: np.ndarray,
                       cell_labels: Optional[np.ndarray] = None,
                       nuclei_labels: Optional[np.ndarray] = None,
                       min_spacing: int = 10,
                       min_radius: int = 2) -> np.ndarray:
        """ Segment a nuclei image

        Split touching nuclei with a watershed transform

        :param ndarray intensity_mask:
            The thresholded nuclei intensity image
        :param ndarray cell_labels:
            Not used by this algorithm
        :param ndarray nuclei_labels:
            Not used by this algorithm
        :param int min_spacing:
            Minimum spacing (in px) between nuclei centers
        :param int min_radius:
            Minimum radius (in px) of an individual nucleus
        :returns:
            A label image where 0 corresponds to background, and values >0 correspond to individual nuclei
        """
        # Find the local centers of the nuclei mask
        intensity_dist = ndi.distance_transform_edt(intensity_mask)
        marker_coords = feature.peak_local_max(
            intensity_dist, min_distance=min_spacing, threshold_abs=min_radius, labels=intensity_mask)
        marker_mask = np.zeros(intensity_dist.shape, dtype=bool)
        marker_mask[tuple(marker_coords.T)] = True

        # Split touching nuclei by their centers
        markers, _ = ndi.label(marker_mask)
        return segmentation.watershed(-intensity_dist, markers, mask=intensity_mask)

    def segment_cells(self,
                      intensity_mask: np.ndarray,
                      cell_labels: Optional[np.ndarray] = None,
                      nuclei_labels: Optional[np.ndarray] = None) -> np.ndarray:
        """ Segment a CellMask or cytoplasm-stained image

        Split cells with a nuclei label image (if provided)

        :param ndarray intensity_mask:
            The thresholded cell intensity image
        :param ndarray cell_labels:
            Not used by this algorithm
        :param ndarray nuclei_labels:
            If not None, assign touching cells to the closest nucleus and remove the nucleus from the cell mask
        :returns:
            A label image where 0 corresponds to background, and values >0 correspond to individual cells
        """
        if nuclei_labels is None:
            # No mask, so just split objects that don't touch
            intensity_labels, _ = ndi.label(intensity_mask)
        else:
            # Watershed to split touching cells and assign to nearest nucleus
            intensity_dist = ndi.distance_transform_edt(nuclei_labels < 0.5)
            intensity_labels = segmentation.watershed(intensity_dist, nuclei_labels, mask=intensity_mask)
            intensity_labels[nuclei_labels > 0.5] = 0  # remove the nucleus from the cell mask
        return intensity_labels

    def segment_mitochondria(self,
                             intensity_mask: np.ndarray,
                             cell_labels: Optional[np.ndarray] = None,
                             nuclei_labels: Optional[np.ndarray] = None) -> np.ndarray:
        """ Segment a TOMM20/mitochondria stained image

        Exclude a nuclei mask and assign individual mitochondria segments to cells (if masks provided)

        :param ndarray intensity_mask:
            The thresholded mitochondria intensity image
        :param ndarray cell_labels:
            If not None, assign labeled mitochondria to a parent cell mask
        :param ndarray nuclei_labels:
            If not None, assign touching cells to the closest nucleus and remove the nucleus from the cell mask
        :returns:
            A label image where 0 corresponds to background, and values >0 correspond to individual mitochondrial clumps
        """

        # Exclude anything in the nucleus and/or outside of the cell mask
        if nuclei_labels is not None:
            intensity_mask[nuclei_labels > 0.5] = 0
        if cell_labels is not None:
            intensity_mask[cell_labels < 0.5] = 0

        # Split the mitochondria into blobs
        intensity_labels, _ = ndi.label(intensity_mask)

        # Try to split the blobs by cell id
        if cell_labels is not None:
            intensity_labels = segmentation.join_segmentations(cell_labels, intensity_labels)
            intensity_labels[intensity_mask < 0.5] = 0  # Discard segments outside of the original mito mask
        return intensity_labels
