#!/usr/bin/env python3
""" Generate the screenshots used for figure 4 """

# Imports
import shutil
import pathlib

# 3rd party
import napari

# Our own imports
from napari_mito_hcs import example_utils

# Constants
FULL_ZOOM = 2.1  # Zoom level for the full view, Figure 4B, C
INSET_ZOOM = 8.0  # Zoom level for the inset view, Figure 4B, C

# Center of the inset view, Figure 4B, C
INSET_CENTER = {
    'spot': (0.0, 344.15769644299723, 806.0154011160973),
    'ridge': (0.0, 344.15769644299723, 806.0154011160973),
}

# Contrast limits for each feature image, Figure 4B, C
CONTRAST_LIMITS = {
    'spot': (0.0, 0.1),
    'ridge': (0.0, 0.2)
}
# width x height in pixels for the output image
SIZE = (1000, 1000)

# From image metadata, X/Y pixel pitch for the example images
UM_PER_PX = 0.29668813247470105  # um/px

# Functions


def screenshot_feature(example_type: str, feature_name: str, outroot: pathlib.Path):
    """ Generate a full screenshot and a zoomed in screenshot of a feature example image

    :param str example_type:
        The example to generate a feature screenshots for (either 'wt' or 'ko')
    :param str feature_name:
        Which example feature image to generate screenshots of
        One of ('spot', 'hole', 'valley', 'saddle', or 'ridge')
    :param Path outroot:
        Directory to save the screenshots to
    """
    feature_image = example_utils.load_example_features(example_type)[feature_name]

    viewer = napari.Viewer(ndisplay=2)
    try:
        r = viewer.add_image(feature_image, name=feature_name, scale=(UM_PER_PX, UM_PER_PX))

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
        viewer.add_shapes([shape], shape_type='path', scale=(UM_PER_PX, UM_PER_PX), edge_width=5, edge_color='white', name='Inset BBox')

        viewer.camera.zoom = FULL_ZOOM/UM_PER_PX

        viewer.screenshot(outroot / f'{feature_name}_full_sb.png', size=SIZE, flash=False, canvas_only=True)

        viewer.scale_bar.visible = False
        viewer.layers['Inset BBox'].visible = False

        viewer.screenshot(outroot / f'{feature_name}_full.png', size=SIZE, flash=False, canvas_only=True)

        viewer.camera.center = (0.0, cx*UM_PER_PX, cy*UM_PER_PX)
        viewer.camera.zoom = INSET_ZOOM/UM_PER_PX

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
        screenshot_feature(
            example_type='wt',
            feature_name=feature_name,
            outroot=outroot,
        )


if __name__ == '__main__':
    main()
