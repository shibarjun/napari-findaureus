# import necessary packages
import numpy as np
from aicsimageio import AICSImage
import czifile as cf
import webcolors
import cv2
import matplotlib.pyplot as plt

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = {}
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                if k not in dd:
                    dd[k] = v
                else:
                    if not isinstance(dd[k], list):
                        dd[k] = [dd[k]]
                    dd[k].append(v)
        d = {t.tag: dd}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

# imag_path_1 = r"C:\Users\mandalshibarjun\Documents\Federike CLSM images\20230307_t00_-01(4)_example 2 (small).czi"
imag_path_2 = r"C:\Users\mandalshibarjun\Documents\171012_bone_IF12_ms59118l_G4_63x_NDD_z-stack60um_tile4x4_highres.czi"
# imag_path_3 = r"C:\Users\mandalshibarjun\Documents\Federike CLSM images\20211123_fixedt0-01(2)_example 1 (big).czi"
imag_path_4 = r"C:\Users\Shibarjun Mandal\Pictures\Saved Pictures\20230307_t00_-01(4)_example 2 (small).ome.tiff"
# numpy_array = cf.imread(imag_path_3)
# czi = cf.CziFile(imag_path_1)
# array_data = czi.asarray()
def ImageList_czi(image_file_numpy_array):
    if len(image_file_numpy_array.shape) == 8:
        try:
            n_d_image = image_file_numpy_array[0, 0, :, 0, :, :, :, :]
            img_check = n_d_image[[1], [0], :, :,:][0]
        except IndexError:
            n_d_image = image_file_numpy_array[0, 0, 0, :, :, :, :, :]
            
    elif len(image_file_numpy_array.shape) == 7:
        n_d_image = image_file_numpy_array[0,0,:,:,:,:,:]
    else:
        n_d_image = None
    return(n_d_image)

# #%% Exploring the different czi metadata
# # Image in different tiles, needs stiching (from Fedrike cell culture)
# img2obejct_1 = AICSImage(imag_path_1)
# scene = img2obejct_1.get_scene(0)
# image_reader_1 = img2obejct_1.reader
# image_data_1 = image_reader_1.data
# image_data_1_sq = image_data_1.squeeze()
# image_channel_names_1 = image_reader_1.channel_names
# img_metadata_1 = img2obejct_1.metadata
# from PIL import Image
# list_of_images = []

# # Iterate over the third dimension
# for i in range(image_data_1_sq.shape[2]):
#     # Append the 2D images to the list
#     list_of_images.append(image_data_1_sq[:,:,i,:,:])
# grid_of_images = np.array(list_of_images).reshape(4, 4, *list_of_images[0].shape)
# img_metadata_dict_1 = etree_to_dict(img_metadata_1)

# #%%
# # Image in one tile, stiching not needed (pelvis bone)
# img2obejct_2 = AICSImage(imag_path_2)
# image_data_2 = img2obejct_2.get_image_data("TZCXY")
# size_xy = img2obejct_2.dims.X,img2obejct_2.dims.Y
# image_channel_names_2 = image_reader_2.channel_names
# img_metadata_2 = img2obejct_2.metadata
# image_data_2_sq = image_data_2.squeeze()
# img_metadata_dict_2 = etree_to_dict(img_metadata_2)

# #%%
# img2obejct_3 = AICSImage(imag_path_3)
# image_reader_3 = img2obejct_3.reader
# image_data_3 = image_reader_1.data

#%%
img2obejct_4 = AICSImage(imag_path_4)
img_metadata_4 = img2obejct_4.metadata
numpy_array = img2obejct_4.get_image_data("TZCXY")
import xmltodict
img_metadata_4_xml = xmltodict.parse(img_metadata_4)
size_xy = img2obejct_4.dims.X,img2obejct_4.dims.Y
scaling_zxy = img2obejct_4.physical_pixel_sizes[0],img2obejct_4.physical_pixel_sizes[1],img2obejct_4.physical_pixel_sizes[2]
channel_size = img2obejct_4.dims.C
z_planes = img2obejct_4.dims.Z
#%%
def ChannelsAvaliable_tiff(image_metadata, channel_size):
    channel_name = []
    channel_colours = []

    if channel_size > 1:
        for ch in range(channel_size):
            channel_name.append(image_metadata['OME']['Image']['Pixels']['Channel'][ch]['@Name'])
            channel_colour = image_metadata['OME']['Image']['Pixels']['Channel'][ch]['@Color']
            try:
                channel_colour = int(channel_colour)
                rgb_color = (channel_colour >> 16 & 255, channel_colour >> 8 & 255, channel_colour & 255)
                color_name = webcolors.rgb_to_name(rgb_color)
            except ValueError:
                color_name = "mixed"
            channel_colours.append(color_name)
    return channel_name, channel_colours

f = ChannelsAvaliable_tiff(img_metadata_4_xml, channel_size)[1]

#%% Read CZI
img_metadata = (cf.CziFile(imag_path_2)).metadata(raw=False)
dict_str = img_metadata['ImageDocument']['Metadata']['Information']['Application']
name_exmpl = dict_str['Name']+" ("+dict_str['Version']+")"
#%% Read nd2
nd2object = AICSImage(r"C:\Users\Shibarjun Mandal\Downloads\nd005.nd2")
img_metadata = nd2object.metadata
img_metadata = etree_to_dict(img_metadata)
metadata_dict = vars(nd2object)
#%% Read lif
lifobject = AICSImage(r"C:\Users\Shibarjun Mandal\Downloads\Mausknochen.lif")
img_metadata = etree_to_dict(lifobject.metadata)
