# Napari MitoHCS Plugin

`napari-mito-hcs` is a plugin for [napari](https://napari.org/stable/) that helps analyze high-content images of mitochondira. It allows you to segment nuclei, cells, mitochondira, and then extract texture features of the mitochondria that can be useful when comparing the state of different cell types.

## Interactive Processing

`napari-mito-hcs` can be accessed from the plugin menu under `Plugins > Mito HCS (napari-mito-hcs)`. Sample data can be loaded from `Open Sample > napari_mito_hcs > Mito HCS Example (WT)`.

![Example Napari Mito HCS Session](docs/images/plugin_example.png "Example Napari Mito HCS Session")

1. Load a nuclei image. In the sample data, this is called `Nucl Image`. Select a threshold to segment the nuclei, then click `Segment Nuclei`.
2. Load a cytoplasm/cell mask stained image. In the sample data, this is called `Cell Image`.  Select a threshold to segment the cells, then click `Segment Cells`. The cell segmentation algorithm will try to use the nuclei segmentation to split touching cells.
3. Load an image stained for mitochondria. In the sample data, this is called `Mito Image`. Select a threshold to segment the mitochondria, then click `Segment Mitochondria`. The mitochondria segmentation algorithm will try to assign mitochondria to individual cells from the cell segmentation.
4. Select which shape index-based texture features to calculate from the mitochondria intensity image. At least `Spot` and `Ridge` must be selected if you want to calculate the spot to ridge ratio feature used by `Mito HCS`. Other features may also be useful for different mitochondrial phenotypes.
5. Set `kernel radius > 0` if you need to subtract a background signal from your mitochondria image before extracting features.
6. Set the smoothing parameter for the image (values between 0.5 and 1.0 tend to work well). Once you're ready click `Calculate Shape Features`.
7. Finally, choose which statistics to save:
    * `Geometry` calculates morphological measurements of mitochondria.
    * `Intensity` calculates average intensity of other stains within the mitochondria.
    * `Texture` calculates average values for the shape index-based texture features.
  `Geometry` and `Texture` must be selected to calculate the final spot to ridge ratio feature used by `Mito HCS`.  Other statistics may also be useful for different mitochondrial phenotypes.
8. Click `Save Stats` to save per-mitochondria measurements to an Excel spreadsheet.

Test out the segmentation pipeline on a few images from your data set (for instance, try the same parameters on `Open Sample > napari_mito_hcs > Mito HCS Example (KO)`). Once you're happy with how the pipeline performs on several images, select `Save Config` to write the parameters out to a TOML file that can be used for batch processing.

If you have parameters saved from a previous setting, you can reload them using the `Load Config`.

## Batch Processing

Once you have the parameters for your segmentation pipeline, you can use them to segment an entire directory of images with the `mito-hcs-batch` script. Given a folder of images located at `path/to/data` and a config file at `path/to/config.toml`, you can run the script with:

```{bash}
mito-hcs-batch --config-file path/to/config.toml path/to/data
```

Results will be writen to the folder `path/to/data/mito-hcs`. Run the command `mito-hcs-batch --help` to see additional options.

## Installing

`napari-mito-hcs` has been tested with Python 3.11 on Windows, OS X, and Linux. It may work on other python versions and operating systems with some modifications.

## Installing from Source

We recommend installing `napari-mito-hcs` into a virtual environment. To create a fresh virtual environment, if on Linux/OS X, run:

    python -m venv ~/mito_hcs_env
    source  ~/mito_hcs_env/bin/activate

If on Windows, instead do:

    python -m venv mito_hcs_env
    mito_hcs_env\Scripts\activate

Next install `napari` and `napari-mito-hcs` and dependencies:

    python -m pip install "napari[all]"
    python -m pip install .

Finally launch `napari`. The tools provided by `napari-mito-hcs` will be available under `Plugins > Mito-HCS`:

    napari

## Running the tests

napari-mito-hcs comes with a test suite. To run the tests first install the test dependencies:

    python -m pip install '.[test]'

Then run:

    python -m pytest tests/

## Building the API documentation

napari-mito-hcs comes with API documentation. To build the documentation from source, install the documentation dependencies:

    python -m pip install '.[docs]'

If on Linux/OS X, run:

    cd docs
    make html

If on Windows, run:

    cd docs
    make.bat html

The built documentation should now be found under `docs/_build/index.html`.

## Citing

If `napari-mito-hcs` has been useful in your research, consider citing

> Chin et al, ...
