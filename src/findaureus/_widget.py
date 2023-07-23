"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
import numpy as np
from typing import TYPE_CHECKING
from .Module_Class import ReadImage
# from ReadImage import FindBacteriaAndNoBacteria
import napari.layers
# from ._reader.py import napari_get_reader
from magicgui import magic_factory
from magicgui.widgets import FileEdit
from pathlib import Path
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
def for_napari(image_list):
    data =np.stack(image_list)
    data = np.expand_dims(data, -1)
    data = data.transpose(3,0,1,2)
    # data = np.expand_dims(data, axis=2)
    return(data)

@magic_factory
def Find_Bacteria(img_layer: "napari.layers.Image") -> "napari.types.LayerDataTuple":
    print(f"you have selected {img_layer}")
    # image_class_instance = ReadImage(Path)
    
    image_list = list(img_layer.data[0,:,:,:])
    _,scalez,scalex ,scaley  = img_layer.scale 
    scalexy = (scalex,scaley)
    scalezxy = (scalez,scaley,scalex)
    bac_image_list,bac_image_list_mask, bac_centroid_xy_coordinates, no_bac_dict, bac_pixelwise_xy_coordinates, bacteria_area = ReadImage.FindBacteriaAndNoBacteria(image_list, scalexy)
    # z_value, x_value, y_value = ReadImage.ImageScalingXY
    bac_data_box = for_napari(bac_image_list)
    bac_data_mask = for_napari(bac_image_list_mask)
    # bac_data = np.concatenate ((bac_data_box,bac_data_mask), axis = 2)
    # bac_layer = (bac_data, {"scale": scalezxy,"name": (f"{img_layer.name}_Bbox", f"{img_layer.name}_mask")})
    bac_layer = (bac_data_mask, {"scale": scalezxy,"name": f"{img_layer.name}_Bbox", "opacity":0.5})
    print("Findbac Done")
    return [bac_layer]



# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
# def example_function_widget(img_layer: "napari.layers.Image"):
#     print(f"you have selected {img_layer}")
