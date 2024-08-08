#!/usr/bin/env python3
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
import sys

# Our own imports
from napari_mito_hcs.pipeline import run_mito_hcs_batch_cmd

# Command line interface

if __name__ == '__main__':
    sys.exit(run_mito_hcs_batch_cmd())
