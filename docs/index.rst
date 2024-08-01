Napari MitoHCS
==============

Napari MitoHCS is a plugin for `napari <https://napari.org/stable/>`_ that helps analyze high-content images of mitochondira.
It allows you to segment nuclei, cells, mitochondira, and then extract texture features of the mitochondria that can be useful when comparing the state of different cell types.

Interactive Processing
----------------------

``napari-mito-hcs`` can be accessed from the plugin menu under ``Plugins > Mito HCS (napari-mito-hcs)``.
Sample data can be loaded from ``Open Sample > napari_mito_hcs > Mito HCS Example (WT)``.

.. image:: images/plugin_example.png
   :width: 800
   :alt: Example Napari Mito HCS Session

1. Load a nuclei image.
   In the sample data, this is called ``Nucl Image``.
   Select a threshold to segment the nuclei, then click ``Segment Nuclei``.
2. Load a cytoplasm/cell mask stained image. In the sample data, this is called ``Cell Image``.
   Select a threshold to segment the cells, then click ``Segment Cells``.
   The cell segmentation algorithm will try to use the nuclei segmentation to split touching cells.
3. Load an image stained for mitochondria.
   In the sample data, this is called ``Mito Image``.
   Select a threshold to segment the mitochondria, then click ``Segment Mitochondria``.
   The mitochondria segmentation algorithm will try to assign mitochondria to individual cells from the cell segmentation.
4. Select which shape index-based texture features to calculate from the mitochondria intensity image.
   At least ``Spot`` and ``Ridge`` must be selected if you want to calculate the spot to ridge ratio feature used by ``Mito HCS``.
   Other features may also be useful for different mitochondrial phenotypes.
5. Set ``kernel radius > 0`` if you need to subtract a background signal from your mitochondria image before extracting features.
6. Set the smoothing parameter for the image (values between ``0.5`` and ``1.0`` tend to work well).
   Once you're ready click ``Calculate Shape Features``.
7. Finally, choose which statistics to save:
   ``Geometry`` calculates morphological measurements of mitochondria.
   ``Intensity`` calculates average intensity of other stains within the mitochondria.
   ``Texture`` calculates average values for the shape index-based texture features.
   ``Geometry`` and ``Texture`` must be selected to calculate the final spot to ridge ratio feature used by ``Mito HCS``.
   Other statistics may also be useful for different mitochondrial phenotypes.
8. Click ``Save Stats`` to save per-mitochondria measurements to an Excel spreadsheet.

Test out the segmentation pipeline on a few images from your data set
(for instance, try the same parameters on ``Open Sample > napari_mito_hcs > Mito HCS Example (KO)``).
Once you're happy with how the pipeline performs on several images, select ``Save Config`` to write the parameters out to a TOML file that can be used for batch processing.

If you have parameters saved from a previous setting, you can reload them using ``Load Config``.

Batch Processing
----------------

Once you have the parameters for your segmentation pipeline, you can use them to segment an entire directory of images with the ``mito-hcs-batch.py`` script in the ``scripts/`` folder.
Given a folder of images located at ``path/to/images`` and a config file at ``path/to/config.toml``, you can run the script with:

.. code-block:: bash

   mito-hcs-batch --config-file path/to/config.toml path/to/data

Results will be writen to the folder ``path/to/images/mito-hcs``.

Segment a directory and write the outputs to a different location:

.. code-block:: bash

   mito-hcs-batch -o path/to/output path/to/images

Results will be writen to the folder ``path/to/output``.

Run the command ``mito-hcs-batch --help`` to see additional options.

API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   pipeline
   segmentation
   feature
   stats
   widget
   config
   finder
   utils

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
