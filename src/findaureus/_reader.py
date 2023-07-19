"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the Reader specification, but your plugin may choose to
implement multiple readers or even other plugin contributions. see:
https://napari.org/stable/plugins/guides.html?#readers
"""
from .module_needed import *

def napari_get_reader(path):
    """A basic implementation of a Reader contribution.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # if it is a list, it is assumed to be an image stack...
        # so we are only going to look at the first file.
        path = path[0]

    # if we know we cannot read the file, we immediately return None.
    if not path.endswith(".czi"):
        return None

    # otherwise we return the *function* that can read ``path``.
    # return lambda path: reader_function(path), {'path': path}
    return reader_function

def metadata (path):
    
    try:
        inputimagefileobject_norm, inputimagefilenumpyarray_norm, inputimagefilemetadata_norm = ReadFile.ReadImageFile(path)
        return (inputimagefileobject_norm,inputimagefilenumpyarray_norm,inputimagefilemetadata_norm, path)
    except:
        inputimagefilemetadata_exp, inputimagefilenumpyarray_exp = ReadFileException.ReadImageFile(path)
        return (inputimagefilemetadata_exp,inputimagefilenumpyarray_exp, path)


def reader_function(path):
    """Take a path or list of paths and return a list of LayerData tuples.
    
    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.
    
    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.
    
    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of
        layer. Both "meta", and "layer_type" are optional. napari will
        default to layer_type=="image" if not provided
    """
# handle both a string and a list of strings
    
    image_from_channels = []
    try:
        inputimageobject, inputimagenumpyarray, inputimagemetadata,_ = metadata(path)
        channels = ReadFile.ChannelColor(path)
    except:
        inputimagemetadata, inputimagenumpyarray,_ = metadata(path)
        channels = ReadFileException.No_ChannelsAvaliable(inputimagemetadata)
        z_value, x_value, y_value = ReadFileException.ImageScalingXY(inputimagemetadata)
        for channel_no in range(0, len(channels)):
            channelimagelist = ReadFileException.ChannelImageList(inputimagenumpyarray, channel_no)
            image_from_channels.append((channelimagelist))
    else:
        z_value, x_value, y_value = ReadFile.ImageScalingXY(inputimageobject)
        for channel_no in range(0, len(channels)):
            channelimagelist = ReadFile.ChannelImageList(inputimagenumpyarray, channel_no)
            image_from_channels.append((channelimagelist))
            
    data = np.stack(image_from_channels)
    data = np.expand_dims(data, -1)
    data = data.transpose(4,1,0,2,3)
    # optional kwargs for the corresponding viewer.add_* method
    if z_value==0:
        
        add_kwargs = {"scale": (y_value,x_value),"channel_axis": 2, "name": channels}
    else:
        add_kwargs = {"scale": (z_value,y_value,x_value),"channel_axis": 2,"name": channels}
    # add_kwargs = {}
    layer_type = "image"  # optional, default is "image"
    
    return [(data, add_kwargs, layer_type)]
