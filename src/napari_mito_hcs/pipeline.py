""" Integrated Mito HCS pipeline

The entire pipeline is encapsulated in the :py:class:`MitoHCSPipeline` class.

To run a complete analysis on a folder using the default settings:

.. code-block:: python

    indir = 'path/to/images'
    outdir = 'path/to/output/images'

    pipeline = MitoHCSPipeline.load_default('mito-hcs')

    for image_files in pipeline.group_files(indir, outdir):
        pipeline.segment_nuclei(image_files)
        pipeline.segment_cells(image_files)
        pipeline.segment_mitochondria(image_files)

        pipeline.calc_features(image_files)

        pipeline.save_stats(image_files)
    pipeline.calc_summary_stats(outdir)

If you don't need to make modifications to the individual pipeline steps, you can
also just call :py:func:`run_mito_hcs_batch` (which performs the same steps as above):

.. code-block:: python

    indir = 'path/to/images'
    outdir = 'path/to/output/images'
    config_file = 'path/to/config.toml'  # or None for the default 'mito-hcs' pipeline

    run_mito_hcs_batch(
        indir=indir,
        outdir=outdir,
        config_file=config_file,
    )

A command line tool is also available under ``scripts/mito-hcs-batch.py``:

.. code-block:: bash

    mito-hcs-batch.py path/to/images \\
        --outdir path/to/output/images \\
        --config-file path/to/config.toml

See the online help of ``mito-hcs-batch.py --help`` for details and other options.

Classes:

* :py:class:`MitoHCSPipeline`: Main class for all stages of the Mito HCS workflow

Functions:

* :py:class:`run_mito_hcs_batch`: Run the entire pipeline using the provided paths

"""

# Imports
import pathlib
from typing import Dict, Any, Generator, Optional

# 3rd party
import numpy as np

import pandas as pd

import tifffile

# Our own imports
from .finder import FileFinder, FileGroup
from .segmentation import SegmentationPipeline
from .feature import ShapeIndexPipeline
from .config import Configurable
from .stats import StatExtractor, summarize_stats

# Classes


class MitoHCSPipeline(Configurable):
    """ Main class for all stages of the Mito HCS workflow

    :param dict[str, any] find_file_params:
        Parameters to pass to the file finding class
    :param dict[str, any] seg_nuclei_params:
        Parameters to pass to the nuclei segmentation class
    :param dict[str, any] seg_cell_params:
        Parameters to pass to the cell segmentation class
    :param dict[str, any] seg_mitochondria_params:
        Parameters to pass to the mitochondria segmentation class
    :param dict[str, any] shape_index_params:
        Parameters to pass to the shape index featurization class
    :param dict[str, any] stat_params:
        Parameters to pass to the stat extraction class

    Segmentation Stages:

    * :py:meth:`group_files`: Search a folder for groups of images (fields of view) to process
    * :py:meth:`segment_nuclei`: Segment the nuclei image
    * :py:meth:`segment_cells`: Segment the cell image
    * :py:meth:`segment_mitochondria`: Segment the mitochondria image
    * :py:meth:`calc_features`: Calculate the featuere images for the mitochondria image
    * :py:meth:`save_stats`: Save the per-mitochondria cluster statistics for this field of view
    * :py:meth:`calc_summary_stats`: Calculate per-field of view summary stats

    Helper Methods:

    * :py:meth:`load_image`: Load an image from a path
    * :py:meth:`save_image`: Save an image to a path
    * :py:meth:`have_image`: See if we have an image already

    """

    def __init__(self,
                 find_file_params: Dict[str, Any],
                 seg_nuclei_params: Dict[str, Any],
                 seg_cell_params: Dict[str, Any],
                 seg_mitochondria_params: Dict[str, Any],
                 shape_index_params: Dict[str, Any],
                 stat_params: Dict[str, Any]):
        self.find_file_params = find_file_params

        self.seg_nuclei_params = seg_nuclei_params
        self.seg_cell_params = seg_cell_params
        self.seg_mitochondria_params = seg_mitochondria_params

        self.shape_index_params = shape_index_params

        self.stat_params = stat_params

        self._cache = {}

    def load_image(self, image_file: pathlib.Path) -> np.ndarray:
        """ Load the image file, using a cache to speed access if possible

        :param Path image_file:
            The image file to load
        :returns:
            The numpy array for that image
        """
        image = self._cache.get(image_file)
        if image is not None:
            return image
        image = tifffile.imread(image_file)
        self._cache[image_file] = image
        return image

    def save_image(self, image_file: pathlib.Path, image: np.ndarray):
        """ Save the image file, using a cache to speed access if possible

        :param Path image_file:
            The image file to save to
        :param Path image:
            The numpy array to save
        """
        image_file.parent.mkdir(parents=True, exist_ok=True)
        tifffile.imwrite(image_file, image)
        self._cache[image_file] = image

    def have_image(self, image_file: pathlib.Path) -> bool:
        """ See if the image file is already generated

        :param Path image_file:
            The image file to find
        :returns:
            True if we already have the image and False otherwise
        """
        if image_file in self._cache:
            return True
        return image_file.is_file()

    # Segmentation stages

    def group_files(self,
                    indir: pathlib.Path,
                    outdir: pathlib.Path) -> Generator[FileGroup, None, None]:
        """ Find all the image files under a directory and group them into paths to process

        :param Path indir:
            The directory where individual channel images can be found for (potentially multiple) field of view
        :param Path outdir:
            The directory to write outputs for each field of view to
        :returns:
            A generator of FileGroup objects that contain the input and output paths for each field of view
        """
        finder = FileFinder(**self.find_file_params)
        for image_files in finder(indir=indir, outdir=outdir):
            yield image_files

    def segment_nuclei(self, image_files: FileGroup):
        """ Nuclei segmentation stage

        :param FileGroup image_files:
            The file group object for this image
        """
        # Work out paths for the output directory
        nuclei_label_path = image_files.get_segmentation_path('nuclei')

        if self.have_image(nuclei_label_path):
            return

        pipeline = SegmentationPipeline(**self.seg_nuclei_params)

        nuclei_image = self.load_image(image_files.nuclei_image)
        nuclei_labels = pipeline(intensity_image=nuclei_image)

        self.save_image(nuclei_label_path, nuclei_labels)

    def segment_cells(self, image_files: FileGroup):
        """ Cell segmentation stage

        :param FileGroup image_files:
            The file group object for this image
        """
        # Work out paths for the output directory
        cell_label_path = image_files.get_segmentation_path('cell')
        nuclei_label_path = image_files.get_segmentation_path('nuclei')

        if self.have_image(cell_label_path):
            return

        pipeline = SegmentationPipeline(**self.seg_cell_params)

        nuclei_labels = self.load_image(nuclei_label_path)
        cell_image = self.load_image(image_files.cell_image)

        cell_labels = pipeline(intensity_image=cell_image,
                               nuclei_labels=nuclei_labels)

        self.save_image(cell_label_path, cell_labels)

    def segment_mitochondria(self, image_files: FileGroup):
        """ Mitochondria segmentation stage

        :param FileGroup image_files:
            The file group object for this image
        """
        # Work out paths for the output directory
        mitochondria_label_path = image_files.get_segmentation_path('mitochondria')
        cell_label_path = image_files.get_segmentation_path('cell')
        nuclei_label_path = image_files.get_segmentation_path('nuclei')

        if self.have_image(mitochondria_label_path):
            return

        pipeline = SegmentationPipeline(**self.seg_mitochondria_params)

        nuclei_labels = self.load_image(nuclei_label_path)
        cell_labels = self.load_image(cell_label_path)
        mitochondria_image = self.load_image(image_files.mitochondria_image)

        mitochondria_labels = pipeline(intensity_image=mitochondria_image,
                                       nuclei_labels=nuclei_labels,
                                       cell_labels=cell_labels)

        self.save_image(mitochondria_label_path, mitochondria_labels)

    def calc_features(self, image_files: FileGroup):
        """ Shape index feature stage

        :param FileGroup image_files:
            The file group object for this image
        """
        pipeline = ShapeIndexPipeline(**self.shape_index_params)

        feature_files = [image_files.get_feature_path(feature_name)
                         for feature_name in pipeline.features]
        if all([self.have_image(feature_file) for feature_file in feature_files]):
            return

        mitochondria_image = self.load_image(image_files.mitochondria_image)

        feature_images = pipeline(mitochondria_image)
        assert len(feature_files) == feature_images.shape[2]

        for i, feature_file in enumerate(feature_files):
            self.save_image(feature_file, feature_images[:, :, i])

    def save_stats(self, image_files: FileGroup):
        """ Shape index feature stage

        :param FileGroup image_files:
            The file group object for this image
        """
        stat_file = image_files.stat_file
        if stat_file.is_file():
            return

        mitochondria_label_path = image_files.get_segmentation_path('mitochondria')
        cell_label_path = image_files.get_segmentation_path('cell')

        feature_paths = image_files.find_feature_paths()

        pipeline = StatExtractor(**self.stat_params)

        mitochondria_labels = self.load_image(mitochondria_label_path)
        cell_labels = self.load_image(cell_label_path)

        # Convert images to a single intensity stack
        if 'intensity' in pipeline.stats:
            intensity_images = {
                'Nuclei': self.load_image(image_files.nuclei_image),
                'Cell': self.load_image(image_files.cell_image),
                'Mitochondira': self.load_image(image_files.mitochondria_image),
            }
        else:
            intensity_images = None

        if 'texture' in pipeline.stats:
            texture_images = {feature_name.capitalize(): self.load_image(feature_path)
                              for feature_name, feature_path in feature_paths.items()}
        else:
            texture_images = None

        # Extract the features and write to disk
        stat_df = pipeline(
            label_image=mitochondria_labels,
            intensity_images=intensity_images,
            texture_images=texture_images,
            parent_label_image=cell_labels,
        )
        stat_file.parent.mkdir(parents=True, exist_ok=True)
        stat_df.to_excel(stat_file, index=False)

    def calc_summary_stats(self, outdir: pathlib.Path,
                           stat_file: Optional[pathlib.Path] = None):
        """ Calculate the summary stats over all FOVs

        :param Path outdir:
            A directory with at least one FOV processed with the pipeline stages above
        :param Path stat_file:
            If not None, path to save the final statistics to (default: outdir / 'mito-hcs-stats.xlsx')
        """
        if stat_file is None:
            stat_file = outdir / 'mito-hcs-stats.xlsx'

        all_df = []
        for subdir in outdir.iterdir():
            if subdir.name.startswith(('.', '~', '$')):
                continue
            sub_stat_file = subdir / 'stats.xlsx'
            if not sub_stat_file.is_file():
                continue
            df = pd.read_excel(sub_stat_file)
            df['Prefix'] = subdir.name
            all_df.append(df)

        # Summarize the final stats and save the output
        all_df = summarize_stats(all_df)
        stat_file.parent.mkdir(parents=True, exist_ok=True)
        all_df.to_excel(stat_file, index=False)

# Functions


def run_mito_hcs_batch(indir: pathlib.Path,
                       outdir: Optional[pathlib.Path] = None,
                       config_file: Optional[pathlib.Path] = None):
    """ Run the Mito HCS pipeline on a batch folder of images

    :param Path indir:
        Path to the directory with images to segment and analyze
    :param Path outdir:
        If not None, path to the directory to write output files to (default: ``indir / 'mito-hcs'``)
    :param Path config_file:
        If not None, path to the config file to load for processing the batch (default: ``mito-hcs.toml`` default config)
    """
    if outdir is None:
        outdir = indir / 'mito-hcs'

    if config_file is None:
        pipeline = MitoHCSPipeline.load_default('mito-hcs')
    else:
        pipeline = MitoHCSPipeline.load_config_file(config_file)

    for image_files in pipeline.group_files(indir, outdir):
        pipeline.segment_nuclei(image_files)
        pipeline.segment_cells(image_files)
        pipeline.segment_mitochondria(image_files)

        pipeline.calc_features(image_files)

        pipeline.save_stats(image_files)
    pipeline.calc_summary_stats(outdir)
