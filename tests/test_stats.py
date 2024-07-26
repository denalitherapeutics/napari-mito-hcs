""" Tests for the stats module """

# Imports
import unittest

# 3rd party
import pandas as pd

import numpy as np

# Our own imports
from napari_mito_hcs import stats

# Tests


class TestStatExtractor(unittest.TestCase):

    def test_can_extract_geometric_features(self):

        label_image = np.zeros((128, 128), dtype=np.uint8)
        label_image[10:20, 20:30] = 1
        label_image[30:50, 30:40] = 2

        extractor = stats.StatExtractor(stats='geometry')
        res_df = extractor(label_image)

        exp_df = pd.DataFrame({
            'ID': [1, 2],
            'PositionX': [14.5, 39.5],
            'PositionY': [24.5, 34.5],
            'Area': [100.0, 200.0],
            'ConvexArea': [100.0, 200.0],
            'MajorAxisLength': [11.48912529, 23.06512519],
            'MinorAxisLength': [11.48912529, 11.48912529],
            'Perimeter': [36.0, 56.0],
            'Solidity': [1.0, 1.0],
            'EquivalentDiameter': [11.283792, 15.957691],
            'Eccentricity': [0.0, 0.86711],
        })
        pd.testing.assert_frame_equal(res_df, exp_df, check_like=True)

    def test_can_extract_intensity_features(self):

        label_image = np.zeros((128, 128), dtype=np.uint8)
        label_image[10:20, 20:30] = 1
        label_image[30:50, 30:40] = 2

        intensity_image0 = np.zeros((128, 128))
        intensity_image0[10:20, 20:30] = 100
        intensity_image0[30:50, 30:40] = 250

        intensity_image1 = np.zeros((128, 128))
        intensity_image1[10:20, 20:30] = 250
        intensity_image1[30:50, 30:40] = 50

        extractor = stats.StatExtractor(stats='intensity')
        res_df = extractor(label_image, intensity_images=[intensity_image0, intensity_image1])

        exp_df = pd.DataFrame({
            'ID': [1, 2],
            'IntensityMean_Ch=0': [100.0, 250.0],
            'IntensityMean_Ch=1': [250.0, 50.0],
        })
        pd.testing.assert_frame_equal(res_df, exp_df, check_like=True)

    def test_can_extract_texture_features_with_custom_names(self):

        label_image = np.zeros((128, 128), dtype=np.uint8)
        label_image[10:20, 20:30] = 1
        label_image[30:50, 30:40] = 2

        texture_image0 = np.zeros((128, 128))
        texture_image0[10:20, 20:30] = 100
        texture_image0[30:50, 30:40] = 250

        texture_image1 = np.zeros((128, 128))
        texture_image1[10:20, 20:30] = 150
        texture_image1[30:50, 30:40] = 250

        extractor = stats.StatExtractor(stats='texture')
        res_df = extractor(label_image, texture_images={'Spot': texture_image0, 'Ridge': texture_image1})

        exp_df = pd.DataFrame({
            'ID': [1, 2],
            'TextureMean_Spot': [100.0, 250.0],
            'TextureMean_Ridge': [150.0, 250.0],
        })

        pd.testing.assert_frame_equal(res_df, exp_df, check_like=True)

    def test_can_extract_parent_child_relationships(self):

        parent_label_image = np.zeros((128, 128), dtype=np.uint8)
        parent_label_image[10:20, 20:30] = 1
        parent_label_image[30:50, 30:40] = 2

        label_image = np.zeros((128, 128), dtype=np.uint8)
        label_image[10:15, 20:25] = 1  # child of id == 1
        label_image[15:21, 25:31] = 2  # child of id == 1, slightly mis-aligned
        label_image[30:40, 30:35] = 3  # child of id == 2
        label_image[40:50, 35:40] = 4  # child of id == 2
        label_image[50:55, 40:45] = 5  # child of id == 0, discard

        extractor = stats.StatExtractor(stats=[])
        res_df = extractor(label_image, parent_label_image=parent_label_image)

        for key in res_df.columns:
            print(key, res_df[key].values)

        # Note that label 5 is discarded because it has parent_id == 0
        exp_df = pd.DataFrame({
            'ID': [1, 2, 3, 4],
            'ParentID': [1, 1, 2, 2],
        })
        pd.testing.assert_frame_equal(res_df, exp_df, check_like=True)

    def test_can_summarize_stats_by_area(self):

        df1 = pd.DataFrame({
            'Prefix': ['r01c02f02'],
            'ID': [1],
            'PositionX': [35.5],
            'PositionY': [75.0],
            'Area': [150.0],
            'ConvexArea': [175.0],
            'MajorAxisLength': [24.0],
            'MinorAxisLength': [20.0],
            'Perimeter': [50.0],
            'Solidity': [0.5],
            'EquivalentDiameter': [13.0],
            'Eccentricity': [0.5],
            'IntensityMean_Ch=0': [125.0],
            'IntensityMean_Ch=1': [175.0],
        })
        df2 = pd.DataFrame({
            'Prefix': ['r01c02f01', 'r01c02f01'],
            'ID': [1, 2],
            'PositionX': [14.5, 39.5],
            'PositionY': [24.5, 34.5],
            'Area': [100.0, 300.0],
            'ConvexArea': [100.0, 350.0],
            'MajorAxisLength': [11.5, 23.0],
            'MinorAxisLength': [11.5, 11.5],
            'Perimeter': [36.0, 56.0],
            'Solidity': [1.0, 1.0],
            'EquivalentDiameter': [11.0, 16.0],
            'Eccentricity': [0.0, 0.8],
            'IntensityMean_Ch=0': [100.0, 250.0],
            'IntensityMean_Ch=1': [250.0, 50.0],
        })
        all_dfs = [df1, df2]

        res_df = stats.summarize_stats(all_dfs, key_column='Prefix', norm_column='Area')

        # Values are sorted by the
        exp_df = pd.DataFrame({
            'Prefix': ['r01c02f01', 'r01c02f02'],
            'Area': [200.0, 150.0],
            'ConvexArea': [225.0, 175.0],
            'MajorAxisLength': [17.25, 24.0],
            'MinorAxisLength': [11.5, 20.0],
            'Perimeter': [46.0, 50.0],
            'Solidity': [1.0, 0.5],
            'EquivalentDiameter': [13.5, 13.0],
            'Eccentricity': [0.4, 0.5],
            'IntensityMean_Ch=0': [212.5, 125.0],
            'IntensityMean_Ch=1': [100.0, 175.0],
            'Count': [2, 1],
            'AspectRatio': [1.5, 1.2],
        })
        pd.testing.assert_frame_equal(res_df, exp_df, check_like=True)

    def test_can_summarize_stats_by_count(self):

        df1 = pd.DataFrame({
            'Prefix': ['r01c02f02'],
            'ID': [1],
            'PositionX': [35.5],
            'PositionY': [75.0],
            'Area': [150.0],
            'ConvexArea': [175.0],
            'MajorAxisLength': [24.0],
            'MinorAxisLength': [20.0],
            'Perimeter': [50.0],
            'Solidity': [0.5],
            'EquivalentDiameter': [13.0],
            'Eccentricity': [0.5],
            'TextureMean_Spot': [125.0],
            'TextureMean_Ridge': [175.0],
        })
        df2 = pd.DataFrame({
            'Prefix': ['r01c02f01', 'r01c02f01'],
            'ID': [1, 2],
            'PositionX': [14.5, 39.5],
            'PositionY': [24.5, 34.5],
            'Area': [100.0, 300.0],
            'ConvexArea': [100.0, 350.0],
            'MajorAxisLength': [11.5, 23.0],
            'MinorAxisLength': [11.5, 11.5],
            'Perimeter': [36.0, 56.0],
            'Solidity': [1.0, 1.0],
            'EquivalentDiameter': [11.0, 16.0],
            'Eccentricity': [0.0, 0.8],
            'TextureMean_Spot': [100.0, 250.0],
            'TextureMean_Ridge': [250.0, 50.0],
        })
        all_dfs = [df1, df2]

        res_df = stats.summarize_stats(all_dfs, key_column='Prefix', norm_column='Count')

        # Values are sorted by the
        exp_df = pd.DataFrame({
            'Prefix': ['r01c02f01', 'r01c02f02'],
            'Area': [200.0, 150.0],
            'ConvexArea': [225.0, 175.0],
            'MajorAxisLength': [17.25, 24.0],
            'MinorAxisLength': [11.5, 20.0],
            'Perimeter': [46.0, 50.0],
            'Solidity': [1.0, 0.5],
            'EquivalentDiameter': [13.5, 13.0],
            'Eccentricity': [0.4, 0.5],
            'TextureMean_Spot': [175.0, 125.0],
            'TextureMean_Ridge': [150.0, 175.0],
            'TextureMean_SpotRidgeRatio': [1.1666666666666667, 0.7142857142857143],
            'Count': [2, 1],
            'AspectRatio': [1.5, 1.2],
        })
        pd.testing.assert_frame_equal(res_df, exp_df, check_like=True)
