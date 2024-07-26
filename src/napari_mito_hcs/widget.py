""" GUI Interface to Napari

Classes:

* :py:class:`MitoHCSWidget`: Hold the stages of the MitoHCS pipeline
* :py:class:`SegmentationWidget`: UI controls for the segmentation stages of the pipeline
* :py:class:`ShapeIndexWidget`:  UI controls for the feature stages of the pipeline
* :py:class:`StatExtractorWidget`: UI controls to extract final stats from the images

Functions:

* :py:func:`load_wt_fov`: Load the WT example field of view

"""
# Imports
import pathlib
from typing import List, Dict, Any
from functools import partial

# 3rd party
from magicgui import widgets

import napari
from napari.utils.notifications import show_error, show_warning, show_info

# Our own imports
from .pipeline import MitoHCSPipeline
from .segmentation import SegmentationPipeline
from .feature import ShapeIndexPipeline
from .stats import StatExtractor
from .utils import load_example_images

# Widget Classes


class MitoHCSWidget(widgets.Container):
    """ Container for the stages of the MitoHCS pipeline

    :param Viewer viewer:
        The napari.Viewer instance this plugin is loaded in
    """

    def __init__(self, viewer: napari.viewer.Viewer):
        super().__init__()
        self._viewer = viewer

        # Segmentation widgets
        self._nucl_seg = SegmentationWidget(self._viewer)
        self._nucl_seg.label = ''

        self._cell_seg = SegmentationWidget(self._viewer)
        self._cell_seg.label = ''

        self._mito_seg = SegmentationWidget(self._viewer)
        self._mito_seg.label = ''

        # Feature extraction widgets
        self._shape_index = ShapeIndexWidget(self._viewer)
        self._shape_index.label = ''

        self._stats_pipeline = StatExtractorWidget(self._viewer)
        self._stats_pipeline.label = ''

        # Initialize the widgets with the defaults
        pipeline = MitoHCSPipeline.load_default('mito-hcs')
        self.update_params(pipeline)

        # Config load/save
        self._load_config = widgets.PushButton(
            text='Load Config',
        )
        self._save_config = widgets.PushButton(
            text='Save Config',
        )
        self._load_save_container = widgets.Container(
            widgets=[self._load_config, self._save_config],
            labels=False,
            layout='horizontal',
        )

        # Connect signals
        self._load_config.changed.connect(self._on_load_config)
        self._save_config.changed.connect(self._on_save_config)

        # Pack the GUI
        self.extend([
            self._nucl_seg,
            self._cell_seg,
            self._mito_seg,
            self._shape_index,
            self._stats_pipeline,
            self._load_save_container,
        ])

    # Parameter Handling

    def update_params(self, pipeline: MitoHCSPipeline):
        self._nucl_seg.update_params(pipeline.seg_nuclei_params)
        self._cell_seg.update_params(pipeline.seg_cell_params)
        self._mito_seg.update_params(pipeline.seg_mitochondria_params)

        self._shape_index.update_params(pipeline.shape_index_params)
        self._stats_pipeline.update_params(pipeline.stat_params)

    # Signal Handlers

    def _on_load_config(self):
        config_file = widgets.show_file_dialog(
            mode='r',
            caption='Select MitoHCS Config to Load',
            filter='*.toml',
        )
        if config_file is None:
            return

        pipeline = MitoHCSPipeline.load_config_file(config_file)
        self.update_params(pipeline)

        show_info(f'Loaded parameters from {config_file}')

    def _on_save_config(self):
        config_file = widgets.show_file_dialog(
            mode='w',
            caption='Select path to Save MitoHCS Config to',
            filter='*.toml',
        )
        if config_file is None:
            return

        # Load the current settings from the widgets
        pipeline = MitoHCSPipeline.load_default('mito-hcs')
        pipeline.seg_nuclei_params.update(self._nucl_seg._params)
        pipeline.seg_cell_params.update(self._cell_seg._params)
        pipeline.seg_mitochondria_params.update(self._mito_seg._params)

        pipeline.shape_index_params.update(self._shape_index._params)
        pipeline.stat_params.update(self._stats_pipeline._params)

        pipeline.save_config_file(config_file)

        show_info(f'Wrote parameters to {config_file}')


class SegmentationWidget(widgets.Container):
    """ Container for GUI controls for each segmentation step

    :param Viewer viewer:
        The napari.Viewer instance this plugin is loaded in
    """

    def __init__(self, viewer: napari.viewer.Viewer):
        super().__init__()

        self._viewer = viewer

        self._params = {}

        # Create widgets to control the parameters
        self._image_layer_combo = widgets.create_widget(
            label="Image",
            annotation="napari.layers.Image",
        )
        self._threshold_box = widgets.LineEdit(
            label="Threshold",
            value=0,
        )
        self._run_button = widgets.PushButton(
            text='Segment',
        )

        # Connect signals
        self._threshold_box.changed.connect(
            self._on_update_threshold,
        )
        self._run_button.changed.connect(
            self._on_run,
        )

        # Pack the GUI
        self.extend([
            self._image_layer_combo,
            self._threshold_box,
            self._run_button,
        ])

    # Parameter handling

    @property
    def algorithm(self) -> str:
        algorithm = self._params.get('algorithm')
        if algorithm is None:
            return ''
        return algorithm.capitalize()

    def update_params(self, params: Dict[str, Any]):
        """ Update UI controls to reflect changes in the underlaying config

        :param dict[str, any] params:
            The kwargs to pass to a :py:class:`SegmentationPipeline` object
        """
        self._params = params

        self._image_layer_combo.label = f'{self.algorithm} Image'
        self._threshold_box.label = f'{self.algorithm} Threshold'
        self._run_button.text = f'Segment {self.algorithm}'

        self._threshold_box.value = self._params['threshold']

    # Signal Handlers

    def _on_update_threshold(self, threshold: int):
        self._params['threshold'] = int(threshold)

    def _on_run(self):
        # Pull out the selected layers from the napari viewer
        image_layer = self._viewer.layers[self._image_layer_combo.value.name]

        if 'Cells Segmentation' in self._viewer.layers:
            cell_labels = self._viewer.layers['Cells Segmentation'].data
        else:
            cell_labels = None

        if 'Nuclei Segmentation' in self._viewer.layers:
            nuclei_labels = self._viewer.layers['Nuclei Segmentation'].data
        else:
            nuclei_labels = None

        # Run the pipeline
        pipeline = SegmentationPipeline(**self._params)
        labels = pipeline(
            image_layer.data,
            cell_labels=cell_labels,
            nuclei_labels=nuclei_labels,
        )
        # Add the new segmentation layer back
        self._viewer.add_labels(labels, name=f'{self.algorithm} Segmentation')


class ShapeIndexWidget(widgets.Container):
    """ Container for GUI controls for each segmentation step

    :param Viewer viewer:
        The napari.Viewer instance this plugin is loaded in
    :param ShapeIndexPipeline pipeline:
        The segmentation model object for this widget
    """

    def __init__(self, viewer: napari.viewer.Viewer):
        super().__init__()
        self._viewer = viewer

        self._params = {}

        # UI controls
        self._image_layer_combo = widgets.create_widget(
            label="Feature Image",
            annotation="napari.layers.Image",
        )

        checkboxes = {}
        for feature_name in ShapeIndexPipeline.list_available_features():
            checkbox = widgets.CheckBox(value=False, text=feature_name.capitalize())
            checkbox.changed.connect(partial(self._on_checkbox_update, feature_name))
            checkboxes[feature_name] = checkbox
        self._checkboxes = checkboxes

        self._checkbox_container = widgets.Container(
            widgets=list(self._checkboxes.values()),
            layout='horizontal',
            labels=False,
        )
        self._checkbox_container.label = ''

        self._radius_box = widgets.LineEdit(
            label="Kernel Radius",
            value=0,
        )
        self._smoothing_box = widgets.LineEdit(
            label="Smoothing",
            value=0,
        )
        self._run_button = widgets.PushButton(
            text='Calculate Shape Features',
        )

        # Connect signals
        self._radius_box.changed.connect(
            self._on_update_radius,
        )
        self._smoothing_box.changed.connect(
            self._on_update_smoothing,
        )
        self._run_button.changed.connect(
            self._on_run,
        )

        # Pack the GUI
        self.extend([
            self._image_layer_combo,
            self._checkbox_container,
            self._radius_box,
            self._smoothing_box,
            self._run_button,
        ])

    # Parameter handling

    def update_params(self, params: Dict[str, Any]):
        self._params = params

        # Update feature selections
        feature_names = self._params['features']
        for feature_name, checkbox in self._checkboxes.items():
            checkbox.value = feature_name in feature_names

        # Update threshold params
        self._radius_box.value = self._params['parabola_height']
        self._smoothing_box.value = self._params['intensity_smoothing']

    # Signal Handlers

    def _on_update_radius(self, threshold: int):
        self._params['parabola_height'] = int(threshold)

    def _on_update_smoothing(self, smoothing: float):
        self._params['intensity_smoothing'] = float(smoothing)

    def _on_checkbox_update(self, feature_name: str, value: bool):
        feature_names = self._params['features']
        if not value and feature_name in feature_names:
            feature_names.remove(feature_name)
        elif value and feature_name not in feature_names:
            feature_names.append(feature_name)
        self._params['features'] = feature_names

    def _on_run(self):
        image_layer = self._viewer.layers[self._image_layer_combo.value.name]

        pipeline = ShapeIndexPipeline(**self._params)
        feature_images = pipeline(
            image_layer.data,
        )
        for i, feature_name in enumerate(pipeline.features):
            feature_image = feature_images[:, :, i]
            self._viewer.add_image(feature_image, name=f'{feature_name.capitalize()} Feature')


class StatExtractorWidget(widgets.Container):
    """ Container for GUI controls for each segmentation step

    :param Viewer viewer:
        The napari.Viewer instance this plugin is loaded in
    :param ShapeIndexPipeline pipeline:
        The segmentation model object for this widget
    """

    def __init__(self, viewer: napari.viewer.Viewer):
        super().__init__()
        self._viewer = viewer

        self._params = {}

        checkboxes = {}
        for stat_name in StatExtractor.list_available_stats():
            checkbox = widgets.CheckBox(value=False, text=stat_name.capitalize())
            checkbox.changed.connect(partial(self._on_checkbox_update, stat_name))
            checkboxes[stat_name] = checkbox
        self._checkboxes = checkboxes

        self._checkbox_container = widgets.Container(
            widgets=list(self._checkboxes.values()),
            layout='horizontal',
            labels=False,
        )
        self._checkbox_container.label = ''

        self._run_button = widgets.PushButton(
            text='Save Stats',
        )
        self._run_button.changed.connect(
            self._on_run,
        )

        # Pack the GUI
        self.extend([
            self._checkbox_container,
            self._run_button,
        ])

    # Parameter Handling

    def update_params(self, params: Dict[str, Any]):
        self._params = params

        # Update feature selections
        stat_names = self._params['stats']
        for stat_name, checkbox in self._checkboxes.items():
            checkbox.value = stat_name in stat_names

    # Signal Handlers

    def _on_checkbox_update(self, stat_name: str, value: bool):
        stat_names = self._params['stats']
        if not value and stat_name in stat_names:
            stat_names.remove(stat_name)
        elif value and stat_name not in stat_names:
            stat_names.append(stat_name)
        self._params['stats'] = stat_names

    def _on_run(self):

        save_path = widgets.show_file_dialog(
            mode='w',
            caption='Select path to Save MitoHCS Stats to',
            filter='*.xlsx',
        )
        if save_path is None:
            show_warning('Select a path to save the stats to')
            return

        # Force save path to be a path and to have the '.xlsx' extension
        save_path = pathlib.Path(save_path)
        save_path = save_path.parent / f'{save_path.stem}.xlsx'

        # Pull out the mitochondria labels
        if 'Mitochondria Segmentation' not in self._viewer.layers:
            show_error(f'Cannot find "Mitochondria Segmentation" layer in {[layer.name for layer in self._viewer.layers]}')
            return
        label_image = self._viewer.layers['Mitochondria Segmentation'].data

        # Pull out the cell labels if we can
        if 'Cells Segmentation' in self._viewer.layers:
            parent_label_image = self._viewer.layers['Cells Segmentation'].data
        else:
            show_warning(f'Cannot find "Cells Segmentation" layer in {[layer.name for layer in self._viewer.layers]}')
            parent_label_image = None

        # Pull out the intensity and/or texture images if requested
        intensity_layers = [layer for layer in self._viewer.layers if isinstance(layer, napari.layers.Image)]

        pipeline = StatExtractor(**self._params)

        if 'texture' in pipeline.stats:
            texture_images = {layer.name: layer.data for layer in intensity_layers if layer.name.endswith(' Feature')}
        else:
            texture_images = None
        if 'intensity' in pipeline.stats:
            intensity_images = {layer.name: layer.data for layer in intensity_layers if not layer.name.endswith(' Feature')}
        else:
            intensity_images = None

        # Okay, extract all the features
        stat_df = pipeline(
            label_image=label_image,
            intensity_images=intensity_images,
            texture_images=texture_images,
            parent_label_image=parent_label_image,
        )
        save_path.parent.mkdir(parents=True, exist_ok=True)
        stat_df.to_excel(save_path, index=False)

        show_info(f'Stats saved to "{save_path}"')

# Functions


def load_wt_example_images() -> List[napari.types.LayerData]:
    images = load_example_images('wt')
    # Return in the napari format
    return [(value, {"name": f'{key.capitalize()} Image'}) for key, value in images.items()]


def load_ko_example_images() -> List[napari.types.LayerData]:
    images = load_example_images('ko')
    # Return in the napari format
    return [(value, {"name": f'{key.capitalize()} Image'}) for key, value in images.items()]
