
# Imports
import pathlib
import shutil

# 3rd party
import numpy as np

import tifffile

# Our own imports
from napari_mito_hcs import utils, segmentation, feature

# Functions


def generate_segmentation(example_type: str,
                          outdir: pathlib.Path):
    """ Generate the segmentation examples

    :param str example_type:
        The example to generate a segmentation for
    :param Path outdir:
        Where to write the segmentation data to
    """
    outdir.mkdir(parents=True, exist_ok=True)

    # Load the raw images
    example_images = utils.load_example_images(example_type)

    nucl_image = example_images['nucl']
    cell_image = example_images['cell']
    mito_image = example_images['mito']

    # Segment nuclei
    pipeline = segmentation.SegmentationPipeline.load_default('nuclei')
    nuclei_labels = pipeline(nucl_image)

    pipeline = segmentation.SegmentationPipeline.load_default('cells')
    cell_labels = pipeline(cell_image, nuclei_labels=nuclei_labels)

    pipeline = segmentation.SegmentationPipeline.load_default('mitochondria')
    mito_labels = pipeline(mito_image, cell_labels=cell_labels, nuclei_labels=nuclei_labels)

    # Save the new files
    tifffile.imwrite(outdir / 'nucl_labels.tif', nuclei_labels)
    tifffile.imwrite(outdir / 'mito_labels.tif', mito_labels)
    tifffile.imwrite(outdir / 'cell_labels.tif', cell_labels)


def generate_features(example_type: str,
                      outdir: pathlib.Path):
    """ Generate the feature examples

    :param str example_type:
        The example to generate a feature set for
    :param Path outdir:
        Where to write the feature data to
    """
    outdir.mkdir(parents=True, exist_ok=True)

    # Load the raw images
    example_images = utils.load_example_images(example_type)

    mito_image = example_images['mito']

    pipeline = feature.ShapeIndexPipeline.load_default('shape_index')
    feature_images = pipeline(mito_image)

    # Empirically determined factors to pack the feature images into 16-bits
    scale_factors = {
        'spot': 2500,
        'hole': 900,
        'ridge': 1000,
        'valley': 250,
        'saddle': 1000,
    }
    for i, feature_name in enumerate(pipeline.features):
        feature_image = feature_images[:, :, i]

        feature_image = np.round(feature_image * scale_factors[feature_name])
        feature_image[feature_image < 0] = 0
        feature_image[feature_image > 65535] = 65535
        feature_image = feature_image.astype(np.uint16)
        tifffile.imwrite(outdir / f'{feature_name}_feature.tif', feature_image)

# Command-line Interface


def main():

    outroot = pathlib.Path.home() / 'demo_mito_hcs'
    if outroot.is_dir():
        shutil.rmtree(outroot)
    outroot.mkdir(parents=True, exist_ok=True)

    for example_type in ['wt', 'ko']:
        generate_segmentation(example_type, outroot / example_type)
        generate_features(example_type, outroot / example_type)


if __name__ == '__main__':
    main()
