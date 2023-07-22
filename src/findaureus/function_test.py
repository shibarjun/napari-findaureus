from tkinter import Tk, filedialog
from io import BytesIO
import os
import napari
import matplotlib as plt
from src.findaureus._reader.py import napari_get_reader
root = Tk()
root.withdraw()
from src.findaureus.Module_Class import ReadImage
path = filedialog.askopenfilename(title="Select file",filetypes = [("czi, nd2, lif","*.czi;*.nd2;*.lif")])

f = ReadImage(path)
g = f.readczi()
image_array = list(g["image_array"][0,:,1,:,:])
g1 = f.FindBacteriaAndNoBacteria(image_array)
h = f.readnd2()
i = f.readlif()

rf = 
#%%
image_from_channels = []
try:
    inputimagefileobject, inputimagefilenumpyarray, inputimagefilemetadata = ReadFile.ReadImageFile(path)
    channels = ReadFile.ChannelColor(path)
except:
    inputimagefilemetadata, inputimagefilenumpyarray = ReadFileException.ReadImageFile(path)
    channels = ReadFileException.No_ChannelsAvaliable(inputimagefilemetadata)
    z_value, x_value, y_value = ReadFileException.ImageScalingXY(inputimagefilemetadata)
    for channel_no in range(0, len(channels)):
        channelimagelist = ReadFileException.ChannelImageList(inputimagefilenumpyarray, channel_no)
        image_from_channels.append((channelimagelist))
else:
    z_value, x_value, y_value = ReadFile.ImageScalingXY(inputimagefileobject)
    for channel_no in range(0, len(channels)):
        channelimagelist = ReadFile.ChannelImageList(inputimagefilenumpyarray, channel_no)
        image_from_channels.append((channelimagelist))

meta = {"name": channels}

data = np.stack(image_from_channels)
data1 = np.expand_dims(data, -1)
data2 = data1.transpose(4,1,0,2,3)
#%%
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
        inputimagefileobject, inputimagefilenumpyarray, inputimagefilemetadata = ReadFile.ReadImageFile(path)
        channels = ReadFile.ChannelColor(path)
    except:
        inputimagefilemetadata, inputimagefilenumpyarray = ReadFileException.ReadImageFile(path)
        channels = ReadFileException.No_ChannelsAvaliable(inputimagefilemetadata)
        z_value, x_value, y_value = ReadFileException.ImageScalingXY(inputimagefilemetadata)
        for channel_no in range(0, len(channels)):
            channelimagelist = ReadFileException.ChannelImageList(inputimagefilenumpyarray, channel_no)
            image_from_channels.append((channelimagelist))
    else:
        z_value, x_value, y_value = ReadFile.ImageScalingXY(inputimagefileobject)
        for channel_no in range(0, len(channels)):
            channelimagelist = ReadFile.ChannelImageList(inputimagefilenumpyarray, channel_no)
            image_from_channels.append((channelimagelist))
    
    # paths = [path] if isinstance(path, str) else path
    # load all files into array
    # arrays = [np.load(_path) for _path in paths]
    # stack arrays into single array
    data = np.stack(image_from_channels)
    data = np.expand_dims(data, -1)
    data = data.transpose(4,1,0,2,3)
    
    # optional kwargs for the corresponding viewer.add_* method
    if z_value==0:
        
        add_kwargs = {"scale": (y_value,x_value)}
    else:
        add_kwargs = {"scale": (z_value,y_value,x_value)}
    # add_kwargs = {}
    layer_type = "image"  # optional, default is "image"
    
    return [(data, add_kwargs, layer_type)]

daa = reader_function(path)
#%%
def display_arrays(arrays):
    with napari.gui_qt():
        # Create an empty viewer
        viewer = napari.Viewer()

        # Add each array to the viewer
        for i, array in enumerate(arrays):
            # Assuming 'arrays' is a list of NumPy arrays
            viewer.add_image(array, name=f'Array {i+1}')

display_arrays(channelimagelist)

from src.findaureus._reader import *

a = napari_get_reader(path)
