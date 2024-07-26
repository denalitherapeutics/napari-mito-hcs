""" Segment and extract stats for a whole directory of images

Segment a directory with the default settings:

.. code-block:: bash

    python mito-hcs-batch.py path/to/images

``path/to/images`` is a directory containing intensity images corresponding to multiple fields of view.
All images under the path will be segmented using the same settings.

Outputs will be written to a subfolder at ``path/to/images/mito-hcs``.

Segment a directory with custom settings (e.g. generated from the ``napari-mito-hcs`` plugin):

.. code-block:: bash

    python mito-hcs-batch.py --config-file path/to/config.toml path/to/images

Segment a directory and write the outputs to a different location:

.. code-block:: bash

    python mito-hcs-batch.py -o path/to/output path/to/images

See ``mito-hcs-batch.py --help`` for details on additional arguments and usage

"""

# Imports
import pathlib
import argparse

# Our own imports
from napari_mito_hcs.pipeline import run_mito_hcs_batch

# Command line interface


def parse_args(args=None):
    parser = argparse.ArgumentParser('Batch process a directory with the Mito-HCS pipeline')
    parser.add_argument('indir', type=pathlib.Path,
                        help='Path to the directory with images to segment and analyze')
    parser.add_argument('-o', '--outdir', type=pathlib.Path,
                        help='Path to the directory to write output files to (default: ${indir}/mito-hcs)')
    parser.add_argument('-c', '--config-file', type=pathlib.Path,
                        help='Path to the config file to use when processing the images')
    return parser.parse_args(args=args)


if __name__ == '__main__':
    args = parse_args()
    run_mito_hcs_batch(**vars(args))
