""" Tests for the integrated Mito HCS pipeline """

# Imports
import numpy as np

import pandas as pd

import tifffile

# Our own imports
from . import helpers

from napari_mito_hcs import example_utils, pipeline

# Tests


class TestMitoHCSPipeline(helpers.FileSystemTestCase):

    def test_can_load_defaults(self):

        proc = pipeline.MitoHCSPipeline.load_default('mito-hcs')

        assert set(proc.find_file_params.keys()) == {'nuclei_pattern', 'cell_pattern', 'mitochondria_pattern'}

        seg_params = {
            'intensity_smoothing',
            'threshold',
            'smallest_object',
            'largest_hole',
            'binary_smoothing',
            'algorithm',
        }

        assert set(proc.seg_nuclei_params.keys()) == seg_params
        assert set(proc.seg_cell_params.keys()) == seg_params
        assert set(proc.seg_mitochondria_params.keys()) == seg_params

        assert set(proc.shape_index_params.keys()) == {'features', 'intensity_smoothing', 'parabola_height'}

        assert set(proc.stat_params.keys()) == {'stats', 'spacing'}

    # Complete integration test

    def test_can_run_whole_pipeline(self):

        # Load the files
        indir = self.tempdir / 'indir'
        indir.mkdir(parents=True, exist_ok=True)

        intensity_images = example_utils.load_example_images('wt')

        f1 = indir / 'r02c02f01ch1.tif'
        f2 = indir / 'r02c02f01ch2.tif'
        f3 = indir / 'r02c02f01ch3.tif'

        tifffile.imwrite(f1, intensity_images['nucl'])
        tifffile.imwrite(f2, intensity_images['cell'])
        tifffile.imwrite(f3, intensity_images['mito'])

        intensity_images = example_utils.load_example_images('ko')

        f1 = indir / 'r02c05f01ch1.tif'
        f2 = indir / 'r02c05f01ch2.tif'
        f3 = indir / 'r02c05f01ch3.tif'

        tifffile.imwrite(f1, intensity_images['nucl'])
        tifffile.imwrite(f2, intensity_images['cell'])
        tifffile.imwrite(f3, intensity_images['mito'])

        # Write the config file
        proc = pipeline.MitoHCSPipeline.load_default('mito-hcs')
        proc.find_file_params.update({
            'cell_pattern': '(r[0-9]+c[0-9]+f[0-9]+)ch2',
            'nuclei_pattern': '(r[0-9]+c[0-9]+f[0-9]+)ch1',
            'mitochondria_pattern': '(r[0-9]+c[0-9]+f[0-9]+)ch3',
        })
        config_file = self.tempdir / 'mito-hcs.toml'
        proc.save_config_file(config_file)

        outdir = self.tempdir / 'outdir'
        assert not outdir.is_dir()

        # Run the pipeline
        pipeline.run_mito_hcs_batch(
            indir=indir,
            outdir=outdir,
            config_file=config_file,
        )

        # Make sure we create both output folders for the two FOVs
        assert outdir.is_dir()
        res_outdirs = [p for p in sorted(outdir.iterdir()) if p.is_dir()]
        exp_outdirs = [outdir / 'r02c02f01', outdir / 'r02c05f01']

        assert res_outdirs == exp_outdirs

        # Make sure we create the expected files under each FOV
        exp_segmentation_data = {
            'r02c02f01': example_utils.load_example_labels('wt'),
            'r02c05f01': example_utils.load_example_labels('ko'),
        }
        exp_feature_data = {
            'r02c02f01': example_utils.load_example_features('wt'),
            'r02c05f01': example_utils.load_example_features('ko'),
        }

        exp_filenames = {
            'cell_labels.tif', 'nuclei_labels.tif', 'mitochondria_labels.tif',
            'hole_feature.tif', 'saddle_feature.tif', 'spot_feature.tif', 'valley_feature.tif', 'ridge_feature.tif',
            'stats.xlsx',
        }
        for res_outdir in res_outdirs:
            res_files = {p for p in res_outdir.iterdir() if p.is_file()}
            res_filenames = {p.name for p in res_files}
            assert res_filenames == exp_filenames

            # Make sure the calculated segmentations match the example
            exp_seg_data = exp_segmentation_data[res_outdir.name]
            for res_file in res_files:
                if not res_file.stem.endswith('_labels'):
                    continue
                exp_data = exp_seg_data[res_file.name[:4]]
                res_data = tifffile.imread(res_file)

                np.testing.assert_allclose(res_data, exp_data, atol=1e-2, rtol=1e-2)

            # Make sure the calculated features match the example
            exp_feat_data = exp_feature_data[res_outdir.name]
            for res_file in res_files:
                if not res_file.stem.endswith('_feature'):
                    continue
                exp_data = exp_feat_data[res_file.name.split('_', 1)[0]]
                res_data = tifffile.imread(res_file)

                np.testing.assert_allclose(res_data, exp_data, atol=1e-2, rtol=1e-2)

        # Make sure we make the final summary worksheet
        assert (outdir / 'mito-hcs-stats.xlsx').is_file()

        # Make sure we get the expected values for the final Spot/Ridge feature ratio
        res_df = pd.read_excel(outdir / 'mito-hcs-stats.xlsx')

        assert 'Prefix' in res_df.columns
        assert 'TextureMean_SpotRidgeRatio' in res_df.columns

        # WT is column 2, KO is column 5 for this test
        res_prefix = res_df['Prefix'].values
        exp_prefix = np.array(['r02c02f01', 'r02c05f01'])
        np.testing.assert_equal(res_prefix, exp_prefix)

        # SER Ratio increases by ~0.05 from WT -> KO
        res_ratio = res_df['TextureMean_SpotRidgeRatio'].values
        exp_ratio = np.array([0.234269, 0.297974])
        np.testing.assert_allclose(res_ratio, exp_ratio, atol=1e-2, rtol=1e-2)
