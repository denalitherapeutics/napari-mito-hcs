""" Extract stats from segmentation and feature images

Classes:

* :py:class:`StatExtractor`: Extract stats for cell and mitochondria segmentation images

Functions:

* :py:func:`summarize_stats`: Summarize a collection of per-FOV stat files and calculate useful ratios

"""

# Imports
from typing import Optional, Union, List, Dict, Tuple

# 3rd party
import numpy as np

from scipy import stats

from skimage import measure

import pandas as pd

# Helpers


def calc_parent_label(mask: np.ndarray, intensity: np.ndarray) -> int:
    """ Calculate the most common parent label under this mask

    :param ndarray mask:
        The mask from regionprops
    :param ndarray intensity:
        The label image passed to regionprops
    :returns:
        The most common label under the mask
    """
    return int(round(stats.mode(intensity[mask])[0]))

# Classes


class StatExtractor(object):
    """ Extract stats from segmentation and intensity images

    :param list[str] stats:
        A list of stats to calculate for each image
    :param list[float] spacing:
        If not None, the width of pixels (um/px) or a tuple of (um/px, um/px) for the row/col directions
    """

    def __init__(self, stats: Optional[Union[str, List[str]]] = None,
                 spacing: Optional[Union[float, List[float]]] = None):
        if stats is None:
            stats = self.list_available_stats()
        elif isinstance(stats, str):
            stats = [stats]
        self.stats = stats

        if spacing is None:
            spacing = [1.0, 1.0]
        elif isinstance(spacing, (int, float)):
            spacing = [spacing, spacing]
        self.spacing = [float(sx) for sx in spacing]

    def __call__(self,
                 label_image: np.ndarray,
                 intensity_images: Optional[Union[List[np.ndarray], Dict[str, np.ndarray]]] = None,
                 texture_images: Optional[Dict[str, np.ndarray]] = None,
                 parent_label_image: Optional[np.ndarray] = None) -> pd.DataFrame:
        """ Extract the stats from the image

        :param ndarray label_image:
            A 2D rows x cols integer array where 0 is background and ids > 0 are individual segmented objects
        :param dict[str, ndarray] intensity_images:
            If not None, a dictionary of channel_name: data 2D rows x cols intensity images
            It can also be a list of ndarray in which case channels will be named 'Ch=0', 'Ch=1', etc...
        :param dict[str, ndarray] texture_images:
            If not None, a dictionary of feature_name: data 2D rows x cols intensity images
        :param ndarray parent_label_image:
            If not None, a 2D rows x cols integer array where 0 is background and ids > 0 are the parent objects of those in ``label_image``
        :returns:
            A DataFrame where each row corresponds to the measurements for one object
        """
        # Rename columns to standardize names
        properties = [
            'label',
        ]
        column_renames = {
            'label': 'ID',
        }

        # Add geometry features
        if 'geometry' in self.stats:
            properties.extend([
                'centroid', 'area', 'area_convex', 'axis_major_length',
                'axis_minor_length', 'perimeter', 'solidity',
                'equivalent_diameter_area', 'eccentricity',
            ])
            column_renames.update({
                'centroid-0': 'PositionX',
                'centroid-1': 'PositionY',
                'area': 'Area',
                'area_convex': 'ConvexArea',
                'axis_major_length': 'MajorAxisLength',
                'axis_minor_length': 'MinorAxisLength',
                'perimeter': 'Perimeter',
                'solidity': 'Solidity',
                'equivalent_diameter_area': 'EquivalentDiameter',
                'eccentricity': 'Eccentricity',
            })

        # Convert the intensity and texture dictionaries to the expected inputs to regionprops
        final_intensity_image = []
        final_intensity_ct = 0

        # Add intensity features
        if 'intensity' in self.stats:
            if intensity_images is None:
                raise ValueError(f'Expected intensity images to calculate stats {self.stats}')
            # Support unnamed intensity images
            if isinstance(intensity_images, list):
                intensity_images = {f'Ch={i}': data for i, data in enumerate(intensity_images)}

            # Add all the images to the array
            for intensity_name, intensity_image in intensity_images.items():
                if intensity_image.shape != label_image.shape:
                    raise ValueError(f'Expected intensity image with shape {label_image.shape}, got shape: {intensity_image.shape}')
                final_intensity_image.append(intensity_image)
                column_renames[f'intensity_mean-{final_intensity_ct}'] = f'IntensityMean_{intensity_name}'
                final_intensity_ct += 1

        # Add texture features
        if 'texture' in self.stats:
            if texture_images is None:
                raise ValueError(f'Expected texture images to calculate stats {self.stats}')

            # Add all the images to the array
            for texture_name, texture_image in texture_images.items():
                if texture_image.shape != label_image.shape:
                    raise ValueError(f'Expected texture image with shape {label_image.shape}, got shape: {texture_image.shape}')
                final_intensity_image.append(texture_image)
                column_renames[f'intensity_mean-{final_intensity_ct}'] = f'TextureMean_{texture_name}'
                final_intensity_ct += 1

        # Make sure we're going to calculate per-ROI means if requested
        if len(final_intensity_image) > 0:
            if 'intensity_mean' not in properties:
                properties.append('intensity_mean')
            final_intensity_image = np.stack(final_intensity_image, axis=2)
        else:
            final_intensity_image = None

        # Call regionprops to extract the requested features
        df = pd.DataFrame(measure.regionprops_table(
            label_image,
            intensity_image=final_intensity_image,
            properties=properties,
            spacing=self.spacing,
        ))
        df = df.rename(columns=column_renames)

        # Extract the parent ids if possible
        if parent_label_image is not None:
            parent_df = pd.DataFrame(measure.regionprops_table(
                label_image,
                intensity_image=parent_label_image[:, :, np.newaxis],
                properties=('label', ),
                extra_properties=(calc_parent_label, ),
                spacing=self.spacing,
            ))
            parent_df = parent_df.rename(
                columns={'label': 'ID', 'calc_parent_label-0': 'ParentID'})
            df = df.merge(parent_df, on='ID', how='outer', validate='one_to_one')
            df = df[df['ParentID'] > 0].copy()
        return df

    @staticmethod
    def list_available_stats() -> List[str]:
        return ['geometry', 'intensity', 'texture']

# Function


def summarize_stats(all_dfs: List[pd.DataFrame],
                    key_columns: Union[str, List[str]] = 'Prefix',
                    norm_column: str = 'Area',
                    ignore_columns: Tuple[str] = ('ID', 'ParentID', 'PositionX', 'PositionY')) -> pd.DataFrame:
    """ Summarize the stats over all fields of view

    :param list[DataFrame] all_dfs:
        A stack of data frames, one per field of view
    :param str key_columns:
        Which column(s) to use to group the data by
    :param str norm_column:
        Which column to use to normalize the summary data by (typically either 'Count' or 'Area')
    :param tuple[str] ignore_columns:
        Don't include these columns when calculating summary stats
    :returns:
        A new dataframe with one entry per FOV and all the other measurements averaged per-FOV
    """
    if len(all_dfs) < 1:
        raise ValueError(f'Expected at least one FOV, got {all_dfs}')

    # Combine all the images into one dataframe
    all_df = pd.concat(all_dfs, ignore_index=True)
    all_df['Count'] = 1

    if isinstance(key_columns, str):
        key_columns = [key_columns]

    if not all([key_column in all_df.columns for key_column in key_columns]):
        raise KeyError(f'Expected key column "{key_columns}" in {list(all_df.columns)}')

    if norm_column not in all_df.columns:
        raise KeyError(f'Expected normalization column "{norm_column}" in {list(all_df.columns)}')

    value_columns = [column for column in all_df.columns if column not in key_columns and column not in ignore_columns]
    norm_mapping = {}
    for value_column in value_columns:
        if 'Mean' in value_column:
            all_df[value_column] = all_df[value_column] * all_df[norm_column]
            norm_mapping[value_column] = norm_column
        elif value_column == 'Count':
            norm_mapping[value_column] = None
        else:
            norm_mapping[value_column] = 'Count'

    # Calculate weighted sums
    all_df = all_df[key_columns + value_columns].groupby(key_columns, as_index=False).sum()
    norm_df = all_df.copy()

    # Normalize the weighted sums by the sum of the weights
    for value_column, norm_column in norm_mapping.items():
        if norm_column is None:
            continue
        norm_df[value_column] = all_df[value_column] / all_df[norm_column]
    # If we got the correct keys, calculate our feature ratios
    # Column names are in order: numerator, denominator, output
    ratios = [
        ('TextureMean_Spot', 'TextureMean_Ridge', 'TextureMean_SpotRidgeRatio'),
        ('MajorAxisLength', 'MinorAxisLength', 'AspectRatio'),
    ]
    for num_column, denom_column, out_column in ratios:
        if num_column not in norm_df.columns:
            continue
        if denom_column not in norm_df.columns:
            continue
        norm_df[out_column] = norm_df[num_column] / (norm_df[denom_column] + 1e-5)
    return norm_df.sort_values(key_columns)
