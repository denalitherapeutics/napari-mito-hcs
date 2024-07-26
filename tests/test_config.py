""" Tests for the config I/O module """

# Imports
from napari_mito_hcs import config

from . import helpers

# Helpers


class MockPipeline(config.Configurable):

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


# Classes


class TestConfigFiles(helpers.FileSystemTestCase):

    def test_save_load_object(self):

        obj = MockPipeline(
            foo=1, bar=True, biff='123',
        )
        config_file = self.tempdir / 'test.toml'
        assert not config_file.is_file()

        obj.save_config_file(config_file)
        assert config_file.is_file()

        res_obj = MockPipeline.load_config_file(config_file)

        assert res_obj.foo == 1
        assert res_obj.bar
        assert res_obj.biff == '123'

    def test_save_load_object_with_private_attributes(self):

        obj = MockPipeline(
            foo=1, bar=True, biff='123', _bad=5, _also_bad=False,
        )
        config_file = self.tempdir / 'test.toml'
        assert not config_file.is_file()

        obj.save_config_file(config_file)
        assert config_file.is_file()

        res_obj = MockPipeline.load_config_file(config_file)

        assert res_obj.foo == 1
        assert res_obj.bar
        assert res_obj.biff == '123'

        assert not hasattr(res_obj, '_bad')
        assert not hasattr(res_obj, '_also_bad')

    def test_load_cell_defaults(self):

        obj = MockPipeline.load_default('cells')

        # Expected params for the cell segmentation pipeline
        assert obj.intensity_smoothing == 0.5
        assert obj.threshold == 1000
        assert obj.smallest_hole == 100
        assert obj.smallest_object == 200
        assert obj.binary_smoothing == 2
        assert obj.algorithm == 'cells'

    def test_load_nuclei_defaults(self):

        obj = MockPipeline.load_default('nuclei')

        # Expected params for the nuclei segmentation pipeline
        assert obj.intensity_smoothing == 0.5
        assert obj.threshold == 500
        assert obj.smallest_hole == 1000
        assert obj.smallest_object == 200
        assert obj.binary_smoothing == 2
        assert obj.algorithm == 'nuclei'

    def test_load_mitochondria_defaults(self):

        obj = MockPipeline.load_default('mitochondria')

        # Expected params for the mitochondria segmentation pipeline
        assert obj.intensity_smoothing == 0.0
        assert obj.threshold == 5000
        assert obj.smallest_hole == 0
        assert obj.smallest_object == 0
        assert obj.binary_smoothing == 0
        assert obj.algorithm == 'mitochondria'

    def test_loads_shape_index_defaults(self):

        obj = MockPipeline.load_default('shape_index')

        # Expected params for the feature extractor
        assert obj.features == ['spot', 'hole', 'ridge', 'valley', 'saddle']
        assert obj.intensity_smoothing == 0.75
        assert obj.parabola_height == 0
