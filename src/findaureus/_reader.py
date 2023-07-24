"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the Reader specification, but your plugin may choose to
implement multiple readers or even other plugin contributions. see:
https://napari.org/stable/plugins/guides.html?#readers
"""
from .Module_Class import ReadImage
from typing import Sequence, Union
import napari.layers

PathLike = str
PathOrPaths = Union[PathLike, Sequence[PathLike]]



def napari_get_reader(path: PathOrPaths):
    # If we recognize the format, we return the actual reader function
    if isinstance(path, str) and path.endswith((".czi",".nd2",".lif")):
        return reader_function
    # otherwise we return None.
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
#%%
# from .module_needed import *




# def napari_get_reader(path):
#     """A basic implementation of a Reader contribution.

#     Parameters
#     ----------
#     path : str or list of str
#         Path to file, or list of paths.

#     Returns
#     -------
#     function or None
#         If the path is a recognized format, return a function that accepts the
#         same path or list of paths, and returns a list of layer data tuples.
#     """
#     if isinstance(path, list):
#         # reader plugins may be handed single path, or a list of paths.
#         # if it is a list, it is assumed to be an image stack...
#         # so we are only going to look at the first file.
#         path = path[0]

#     # if we know we cannot read the file, we immediately return None.
#     if not path.endswith((".czi",".nd2",".lif")):
#         return None

#     # otherwise we return the *function* that can read ``path``.
#     # return lambda path: reader_function(path), {'path': path}
#     return reader_function

# def reader_function(path):
#     """Take a path or list of paths and return a list of LayerData tuples.
    
#     Readers are expected to return data as a list of tuples, where each tuple
#     is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
#     both optional.
    
#     Parameters
#     ----------
#     path : str or list of str
#         Path to file, or list of paths.
    
#     Returns
#     -------
#     layer_data : list of tuples
#         A list of LayerData tuples where each tuple in the list contains
#         (data, metadata, layer_type), where data is a numpy array, metadata is
#         a dict of keyword arguments for the corresponding viewer.add_* method
#         in napari, and layer_type is a lower-case string naming the type of
#         layer. Both "meta", and "layer_type" are optional. napari will
#         default to layer_type=="image" if not provided
#     """
# # handle both a string and a list of strings
    
#     image_path = ReadImage(path)
#     if path.endswith(".czi"):
#         image_dict = image_path.readczi()
#     if path.endswith(".nd2"):
#         image_dict = image_path.readnd2()
#     if path.endswith(".lif"):
#         image_dict = image_path.readlif()
            
#     data = image_dict["image_array"]
#     if image_dict["scaling_zxy"][0] == 0:
#         metadata = {"scale":image_dict["scaling_zxy"][1:] ,"channel_axis": 2,"name":image_dict["channel_name"] }
#     else:
#         metadata = {"scale":image_dict["scaling_zxy"] ,"channel_axis": 2,"name":image_dict["channel_name"] }
#     # add_kwargs = {}
#     layer_type = "image"  # optional, default is "image"
    
#     return [(data, metadata, layer_type)]

# # path= r"C:/Users/mandalshibarjun/Documents/171012_bone_IF12_ms59118l_G4_63x_NDD_z-stack60um_tile4x4_highres.czi"
# # nrf = napari_get_reader(path)
# # rf = reader_function(path)

