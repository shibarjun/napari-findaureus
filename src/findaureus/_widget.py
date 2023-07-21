"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
import numpy as np
from typing import TYPE_CHECKING
from findaureus.module_needed import *
# from findaureus._reader import metadata
from magicgui import magic_factory
# from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget

if TYPE_CHECKING:
    import napari


# class ExampleQWidget(QWidget):
#     # your QWidget.__init__ can optionally request the napari viewer instance
#     # in one of two ways:
#     # 1. use a parameter called `napari_viewer`, as done here
#     # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
#     def __init__(self, napari_viewer):
#         super().__init__()
#         self.viewer = napari_viewer

#         btn = QPushButton("Click me!")
#         btn.clicked.connect(self._on_click)

#         self.setLayout(QHBoxLayout())
#         self.layout().addWidget(btn)

#     def _on_click(self):
#         print("napari has", len(self.viewer.layers), "layers")


@magic_factory
def Find_Bacteria(img_layer: "napari.layers.Image", path:str) -> "napari.types.LayerDataTuple":
    
    # try:
    #     imgfilemetadata,_,_,_ = metadata(path)
    #     print(f"you have selected {img_layer}")
    # except:
    #     imgfilemetadata,_,_ = metadata(path)
    #     print(f"you have selected {img_layer}")
    
    # bac_image_list, bac_centroid_xy_coordinates, no_bac_dict, bac_pixelwise_xy_coordinates, bacteria_area,file_metadata = FindBacteriaAndNoBacteria(list(img_layer.data[0,:,:,:]), imgfilemetadata)
    # z_value, x_value, y_value = ReadFile.ImageScalingXY(file_metadata)
    # bac_data = np.stack(bac_image_list)
    # bac_data = np.expand_dims(bac_data, -1)
    # bac_data = bac_data.transpose(3,0,1,2)
    # bac_layer = (bac_data, {"scale": (z_value,y_value,x_value),"name": f"{img_layer.name}_bac"})
    pass
    return


# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
# def example_function_widget(img_layer: "napari.layers.Image"):
#     print(f"you have selected {img_layer}")
