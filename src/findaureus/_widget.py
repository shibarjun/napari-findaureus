"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
import numpy as np
from typing import TYPE_CHECKING
from .Module_Class import ReadImage
import napari.layers
from magicgui import magic_factory

if TYPE_CHECKING:
    import napari

def for_napari(image_list):
    data =np.stack(image_list)
    data = np.expand_dims(data, -1)
    data = data.transpose(3,0,1,2)
    return(data)

@magic_factory
def Find_Bacteria(img_layer: "napari.layers.Image") -> "napari.types.LayerDataTuple":
    print(f"you have selected {img_layer}")
    image_list = list(img_layer.data[0,:,:,:])
    _,scalez,scalex ,scaley  = img_layer.scale 
    scalexy = (scalex,scaley)
    scalezxy = (scalez,scaley,scalex)
    bac_image_list_mask= ReadImage.FindBacteriaAndNoBacteria(image_list, scalexy)
    bac_data_mask = for_napari(bac_image_list_mask)
    bac_layer = (bac_data_mask, {"scale": scalezxy,"name": f"{img_layer.name}_Bacteria mask", "opacity":0.5})
    print("Findbac Done")
    return [bac_layer]
