""" Generate the screenshots used for figure 4 """

# Imports
import shutil
import pathlib

# 3rd party
import numpy as np

import napari

# Our own imports
from napari_mito_hcs import utils

# Constants
FULL_ZOOM = 2.1
INSET_ZOOM = 8.0
INSET_CENTER = {
    'spot': (0.0, 344.15769644299723, 806.0154011160973),
    'ridge': (0.0, 344.15769644299723, 806.0154011160973),
}

CONTRAST_LIMITS = {
    'spot': (0.0, 0.1),
    'ridge': (0.0, 0.2)
}
SIZE = (1000, 1000)

# Functions


def screenshot_feature(feature_name: str, feature_image: np.ndarray, outroot: pathlib.Path):
    """ Generate a full screenshot and a zoomed in screenshot

    :param str feature_name:
        Which feature image to generate screenshots of
    :param ndarray feature_image:
        The feature image array
    :param Path outroot:
        Directory to save the screenshots to
    """

    um_per_px = 0.29668813247470105

    viewer = napari.Viewer(ndisplay=2)
    try:
        r = viewer.add_image(feature_image, name=feature_name, scale=(um_per_px, um_per_px))

        viewer.scale_bar.visible = True
        viewer.scale_bar.unit = 'um'
        r.contrast_limits = CONTRAST_LIMITS[feature_name]

        _, cx, cy = INSET_CENTER[feature_name]

        zoom_ratio = FULL_ZOOM / INSET_ZOOM
        hx = zoom_ratio*SIZE[0]*0.5
        hy = zoom_ratio*SIZE[1]*0.5

        shape = [
            (cx - hx, cy - hy),
            (cx - hx, cy + hy),
            (cx + hx, cy + hy),
            (cx + hx, cy - hy),
            (cx - hx, cy - hy),
        ]
        viewer.add_shapes([shape], shape_type='path', scale=(um_per_px, um_per_px), edge_width=5, edge_color='white', name='Inset BBox')

        viewer.camera.zoom = FULL_ZOOM/um_per_px

        viewer.screenshot(outroot / f'{feature_name}_full_sb.png', size=SIZE, flash=False, canvas_only=True)

        viewer.scale_bar.visible = False
        viewer.layers['Inset BBox'].visible = False

        viewer.screenshot(outroot / f'{feature_name}_full.png', size=SIZE, flash=False, canvas_only=True)

        viewer.camera.center = (0.0, cx*um_per_px, cy*um_per_px)
        viewer.camera.zoom = INSET_ZOOM/um_per_px

        viewer.scale_bar.visible = True
        viewer.screenshot(outroot / f'{feature_name}_zoom_sb.png', size=SIZE, flash=False, canvas_only=True)

        viewer.scale_bar.visible = False
        viewer.screenshot(outroot / f'{feature_name}_zoom.png', size=SIZE, flash=False, canvas_only=True)
    finally:
        viewer.close()


# Command-line Interface

def main():

    outroot = pathlib.Path.home() / 'screenshots_mito_hcs'
    if outroot.is_dir():
        shutil.rmtree(outroot)
    outroot.mkdir(parents=True, exist_ok=True)

    for feature_name in ['spot', 'ridge']:
        feature_image = utils.load_example_features('wt')[feature_name]
        screenshot_feature(feature_name, feature_image, outroot)


if __name__ == '__main__':
    main()
