""" File organization for the Mito-HCS pipeline

Classes:

* :py:class:`FileGroup`: Represent a group of files for input and output
* :py:class:`FileFinder`: Organize a directory into logical groups using file name regexes

"""

# Imports
import re
import pathlib
from typing import Union, Dict, Generator
from dataclasses import dataclass

# Our imports
from .config import Configurable

# Constants
IMAGE_SUFFIXES = ('.tif', '.tiff')

# Classes


@dataclass
class FileGroup:
    """ A group of file paths for input and output """

    # Input files
    nuclei_image: pathlib.Path
    cell_image: pathlib.Path
    mitochondria_image: pathlib.Path
    prefix: str

    # Output paths
    outdir: pathlib.Path

    # Calculated paths

    @property
    def stat_file(self) -> pathlib.Path:
        """ Excel file to save the extracted stats to """
        return self.outdir / self.prefix / 'stats.xlsx'

    def get_intensity_path(self, algorithm: str) -> pathlib.Path:
        """ Get the path to the intensity image

        :param str algorithm:
            Which segmentation algorithm should be applied to the image (one of 'nuclei', 'cell', 'mitochondria')
        """
        return self.outdir / self.prefix / f'{algorithm}_image.tif'

    def get_segmentation_path(self, algorithm: str) -> pathlib.Path:
        """ Get the path to the segmentation image

        :param str algorithm:
            Which segmentation algorithm was be applied to the image (one of 'nuclei', 'cell', 'mitochondria')
        """
        return self.outdir / self.prefix / f'{algorithm}_labels.tif'

    def get_feature_path(self, algorithm: str) -> pathlib.Path:
        """ Get the path to the feature image

        :param str algorithm:
            Which feature algorithm is being used (one of 'hole', 'spot', 'ridge', 'valley', 'saddle')
        """
        return self.outdir / self.prefix / f'{algorithm}_feature.tif'

    def find_feature_paths(self) -> Dict[str, pathlib.Path]:
        """ Find all the feature images under the output directory

        :returns:
            A dictionary of feature_name: feature_image_path pairs
        """
        outdir = self.outdir / self.prefix
        if not outdir.is_dir():
            return {}
        feature_paths = {}
        for p in outdir.iterdir():
            if p.name.startswith(('.', '~', '$')):
                continue
            if not p.name.endswith('_feature.tif'):
                continue
            feature_name = p.name.rsplit('_', 1)[0]
            feature_paths[feature_name] = p
        return feature_paths


class FileFinder(Configurable):
    """ Find and group image files under a directory

    Each regex is expected to define a pattern with one named group called "prefix".

    The pattern captured by prefix is used to organize the files into fields of view

    Ex: Assume your files are named "r01c01f01ch1.tif", "r01c01f01ch2.tif", "r01c01f01ch3.tif", etc

    If ch1 is the cell image, ch2 is the nuclei image and ch3 is the mitochondria image, then use the following patterns:

    * ``cell_pattern = '(?P<prefix>r[0-9]+c[0-9]+f[0-9]+)ch1'``
    * ``nuclei_pattern = '(?P<prefix>r[0-9]+c[0-9]+f[0-9]+)ch2'``
    * ``mitochondria_pattern = '(?P<prefix>r[0-9]+c[0-9]+f[0-9]+)ch3'``

    Patterns are case insensitive and should not end with the '.tif' extension

    :param str cell_pattern:
        Regular expression to find cell images
    :param str nuclei_pattern:
        Regular expression to find nuclei images
    :param str mitochondria_pattern:
        Regular expression to find mitochondria images
    """

    def __init__(self,
                 cell_pattern: str,
                 nuclei_pattern: str,
                 mitochondria_pattern: str):
        self.cell_pattern = cell_pattern
        self.nuclei_pattern = nuclei_pattern
        self.mitochondria_pattern = mitochondria_pattern

    def __call__(self,
                 indir: Union[str, pathlib.Path],
                 outdir: Union[str, pathlib.Path]) -> Generator[FileGroup, None, None]:
        """ Find all the files under a folder and generate groups based on regexes

        :param Path indir:
            The directory with cell/nuclei/mitochondria image files
        :param Path outdir:
            The directory to write segmentations, texture images, and stats to
        :returns:
            A generator of grouped files for each collection of files that match the patterns
        """
        # Patterns are tried in order and the first match is returned
        patterns = {
            'cell': re.compile(self.cell_pattern, re.IGNORECASE),
            'nuclei': re.compile(self.nuclei_pattern, re.IGNORECASE),
            'mitochondria': re.compile(self.mitochondria_pattern, re.IGNORECASE)
        }

        # Collect all the image files under the input directory
        grouped_images = {}
        for p in sorted(indir.iterdir()):
            if p.name.startswith(('.', '~', '$')):
                continue
            if not p.name.endswith(IMAGE_SUFFIXES):
                continue
            stem = p.stem
            for pattern_name, pattern in patterns.items():
                match = pattern.match(stem)
                if not match:
                    continue
                # Prefix is the first matching group
                prefix = match.group(1)
                group = grouped_images.setdefault(prefix, {})
                if pattern_name in group:
                    oldp = group[pattern_name]
                    raise ValueError(f'Got non-unqiue {pattern_name} match for {oldp} and {p}')
                group[pattern_name] = p
                break

        # Now convert the complete groups to FileGroup objects
        for prefix, group in grouped_images.items():
            if len(group) != len(patterns):
                continue

            nuclei_image = group['nuclei']
            cell_image = group['cell']
            mitochondria_image = group['mitochondria']
            yield FileGroup(
                nuclei_image=nuclei_image,
                cell_image=cell_image,
                mitochondria_image=mitochondria_image,
                prefix=prefix,
                outdir=outdir,
            )
