""" Tests for the segmentation module """

# Imports
import unittest

# 3rd party
import numpy as np

# Our own imports
from napari_mito_hcs import segmentation, utils

# Tests


class TestSegmentationPipeline(unittest.TestCase):

    # Unit tests

    def test_basic_segmentation(self):

        image = np.zeros((128, 128))
        image[50:100, 40:90] = 100

        pipeline = segmentation.SegmentationPipeline(
            intensity_smoothing=0.0,
            threshold=50,
            smallest_object=-1,
            smallest_hole=-1,
            binary_smoothing=0,
            algorithm='cells',
        )
        res_labels = pipeline(image)

        exp_labels = np.zeros((128, 128), dtype=np.uint8)
        exp_labels[50:100, 40:90] = 1

        np.testing.assert_allclose(res_labels, exp_labels)

    def test_nuclei_segmentation_splits_touching_objects(self):

        # Make two squares with a bridge in between
        image = np.zeros((128, 128))
        image[10:20, 20:30] = 100
        image[14:16, 30:40] = 100
        image[10:20, 40:50] = 100

        pipeline = segmentation.SegmentationPipeline(
            intensity_smoothing=0.0,
            threshold=50,
            smallest_object=-1,
            smallest_hole=-1,
            binary_smoothing=0,
            algorithm='nuclei',
        )
        res_labels = pipeline(image)

        exp_labels = np.zeros((128, 128), dtype=np.uint8)
        exp_labels[10:20, 20:30] = 1
        exp_labels[14:16, 30:35] = 1
        exp_labels[14:16, 35:40] = 2
        exp_labels[10:20, 40:50] = 2

        np.testing.assert_allclose(res_labels, exp_labels)

    def test_mito_segmentation_splits_by_cell_label(self):

        # Make two squares with a bridge in between
        image = np.zeros((128, 128))
        image[10:50, 20:60] = 100

        cell_labels = np.zeros((128, 128), dtype=np.uint8)
        cell_labels[20:50, 30:45] = 1
        cell_labels[20:50, 45:60] = 2

        pipeline = segmentation.SegmentationPipeline(
            intensity_smoothing=0.0,
            threshold=50,
            smallest_object=-1,
            smallest_hole=-1,
            binary_smoothing=0,
            algorithm='mitochondria',
        )
        res_labels = pipeline(image, cell_labels=cell_labels)

        exp_labels = np.zeros((128, 128), dtype=np.uint8)
        exp_labels[20:50, 30:45] = 1
        exp_labels[20:50, 45:60] = 2

        np.testing.assert_allclose(res_labels, exp_labels)

    # Integration Tests

    def test_nuclei_example_matches(self):

        for example in ['wt', 'ko']:
            with self.subTest(example):
                nuclei_image = utils.load_example_images(example)['nucl']

                pipeline = segmentation.SegmentationPipeline.load_default('nuclei')
                res_labels = pipeline(nuclei_image)

                exp_labels = utils.load_example_labels(example)['nucl']

                np.testing.assert_allclose(res_labels, exp_labels)

    def test_cell_example_matches(self):

        for example in ['wt', 'ko']:
            with self.subTest(example):
                cell_image = utils.load_example_images(example)['cell']
                nuclei_labels = utils.load_example_labels(example)['nucl']

                pipeline = segmentation.SegmentationPipeline.load_default('cells')
                res_labels = pipeline(cell_image, nuclei_labels=nuclei_labels)

                exp_labels = utils.load_example_labels(example)['cell']

                np.testing.assert_allclose(res_labels, exp_labels)

    def test_mito_example_matches(self):

        for example in ['wt', 'ko']:
            with self.subTest(example):
                mito_image = utils.load_example_images(example)['mito']
                all_labels = utils.load_example_labels(example)

                nuclei_labels = all_labels['nucl']
                cell_labels = all_labels['cell']

                pipeline = segmentation.SegmentationPipeline.load_default('mitochondria')
                res_labels = pipeline(mito_image, cell_labels=cell_labels, nuclei_labels=nuclei_labels)

                exp_labels = all_labels['mito']

                np.testing.assert_allclose(res_labels, exp_labels)
