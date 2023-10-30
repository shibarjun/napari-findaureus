"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the Reader specification, but your plugin may choose to
implement multiple readers or even other plugin contributions. see:
https://napari.org/stable/plugins/guides.html?#readers
"""
from .Module_Class import *
from typing import Sequence, Union
import napari.layers

PathLike = str
PathOrPaths = Union[PathLike, Sequence[PathLike]]



def napari_get_reader(path: PathOrPaths):
    if isinstance(path, str) and path.endswith((".czi",".nd2",".lif")):
        return reader_function
    return None

def metadata_dict (path: PathOrPaths):
    image_path = ReadImage(path)
    if path.endswith(".czi"):
        image_dict = image_path.readczi()
    if path.endswith(".nd2"):
        image_dict = image_path.readnd2()
    if path.endswith(".lif"):
        image_dict = image_path.readlif()
        
    return(image_dict)

def reader_function(path: PathOrPaths) -> "napari.types.LayerDataTuple":
    
    image_dict = metadata_dict(path)
    data = image_dict["image_array"]
    if image_dict["scaling_zxy"][0] == 0:
        layer_attributes = {"scale":image_dict["scaling_zxy"][1:] ,"channel_axis": 2,"name":image_dict["channel_name"] }
    else:
        layer_attributes = {"scale":image_dict["scaling_zxy"] ,"channel_axis": 2,"name":image_dict["channel_name"] }
    layer_type = "image"  # optional, default is "image"
    return [(data, layer_attributes,layer_type)]