from .Module_Class import ReadImage
from typing import Sequence, Union
import napari.layers

PathLike = str
PathOrPaths = Union[PathLike, Sequence[PathLike]]

def napari_get_reader(path: PathOrPaths):
    if isinstance(path, str) and path.endswith((".czi",".nd2",".lif", ".tiff")):
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
    if path.endswith(".tiff"):
        image_dict = image_path.readtiff()
        
    return(image_dict)

def reader_function(path: PathOrPaths) -> "napari.types.LayerDataTuple":
    
    image_dict = metadata_dict(path)
    data = image_dict["image_array"]
    concatenated_names = []
    for color, name in zip(image_dict["channel_colors"], image_dict["channel_name"]):
        concatenated_names.append(f"{name} ({color})")
    if image_dict["scaling_zxy"][0] == 0:
        layer_attributes = {"scale":image_dict["scaling_zxy"][1:] ,"channel_axis": 2,"name":concatenated_names }
    else:
        layer_attributes = {"scale":image_dict["scaling_zxy"] ,"channel_axis": 2,"name":concatenated_names }
    layer_type = "image"  # optional, default is "image"
    return [(data, layer_attributes,layer_type)]