#import packages
import numpy as np
from aicsimageio import AICSImage
import czifile as cf
import webcolors
import cv2

class ReadImage:
    
    def ClosestColour(requested_colour):
        colours_name = {}
        for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            rd = (r_c - requested_colour[0]) ** 2
            gd = (g_c - requested_colour[1]) ** 2
            bd = (b_c - requested_colour[2]) ** 2
            colours_name[(rd + gd + bd)] = name
        
        return colours_name[min(colours_name.keys())]
    
    def ElementToDict(element):
        dictionary = {element.tag: {}}
        if element.attrib:
            dictionary[element.tag].update({'@' + key: value for key, value in element.attrib.items()})
        if element.text:
            dictionary[element.tag]['#text'] = element.text.strip()
        for child_element in element:
            child_dictionary = ReadImage.ElementToDict(child_element)
            if child_element.tag in dictionary[element.tag]:
                if isinstance(dictionary[element.tag][child_element.tag], list):
                    dictionary[element.tag][child_element.tag].append(child_dictionary[child_element.tag])
                else:
                    dictionary[element.tag][child_element.tag] = [dictionary[element.tag][child_element.tag], child_dictionary[child_element.tag]]
            else:
                dictionary[element.tag].update(child_dictionary)

        return dictionary
    
    def ImageSize_czi (file_metadatadict_for_imagesize):
        image_size_x = int(file_metadatadict_for_imagesize['ImageDocument']['Metadata']['Information']['Image']['SizeX'])
        image_size_y = int(file_metadatadict_for_imagesize['ImageDocument']['Metadata']['Information']['Image']['SizeY'])
        return(image_size_x, image_size_y)
    
    def ChannelsAvaliable_czi(file_metadatadict_for_channel):
        channel_colours = []
        channel_colours_name = []
        channel_size = int(file_metadatadict_for_channel['ImageDocument']['Metadata']['Information']['Image']['SizeC'])
        
        if channel_size == 1:
            channel_colours.append(file_metadatadict_for_channel['ImageDocument']['Metadata']['DisplaySetting']['Channels']['Channel']['Color'])
        if channel_size > 1:
            for ch in range(channel_size):
                channel_colours.append(file_metadatadict_for_channel['ImageDocument']['Metadata']['DisplaySetting']['Channels']['Channel'][ch]['Color'])
        
        for chclr in range (0, len(channel_colours)):
            try:
                if len(channel_colours[chclr])>7:
                    color_new = str('#')+channel_colours[chclr][3:]
                    rgb = webcolors.hex_to_rgb(color_new)
                else:
                    rgb = webcolors.hex_to_rgb(channel_colours[chclr][:7])
                closest_name = actual_name = webcolors.rgb_to_name(rgb)
                channel_colours_name.append(actual_name)
            except ValueError:
                closest_name = ReadImage.ClosestColour(rgb)
                channel_colours_name.append(closest_name)
        
        return(channel_colours_name)
    
    def ChannelsAvaliable_nd2 (image_metadata,channel_size):
        channel_colours = []
        channel_colours_name = []
        if channel_size == 1:
            channel_colours.append(image_metadata["metadata"].channels.channel.colorRGB)
        if channel_size > 1:
            for ch in range(channel_size):
                channel_colours.append(image_metadata["metadata"].channels[ch].channel.colorRGB)
        for chclr in range (0, len(channel_colours)):
            rgb_color = webcolors.hex_to_rgb('#{:06x}'.format(channel_colours[chclr]))
            rgb_name = webcolors.rgb_to_name(rgb_color)
            channel_colours_name.append(rgb_name)
    
    def ChannelsAvaliable_lif (image_metadata,channel_size):
        channel_colours_name = []
        if channel_size == 1:
            channel_colours_name.append(image_metadata['LMSDataContainerHeader']['Element']['Children']['Element'][0]['Data']['Image']["ImageDescription"]["Channels"]["ChannelDescription"]["@LUTName"])
        if channel_size > 1:
            for ch in range(channel_size):
                channel_colours_name.append(image_metadata['LMSDataContainerHeader']['Element']['Children']['Element'][0]['Data']['Image']["ImageDescription"]["Channels"]["ChannelDescription"][ch]["@LUTName"])
        return(channel_colours_name)
    
    def ImageScalingZXY_czi(file_metadatadict_for_scaling):
        scale_x = file_metadatadict_for_scaling['ImageDocument']['Metadata']['Scaling']['Items']['Distance'][0]['Value']
        scale_x = scale_x*10**6
        scale_y = file_metadatadict_for_scaling['ImageDocument']['Metadata']['Scaling']['Items']['Distance'][1]['Value']
        scale_y = scale_y*10**6
        try:
            scale_z = file_metadatadict_for_scaling['ImageDocument']['Metadata']['Scaling']['Items']['Distance'][2]['Value']
            scale_z = scale_z*10**6
        except IndexError:
            scale_z = 1
        return([scale_z, scale_x, scale_y])
    
    def ZPlanes_czi(file_metadatadict_for_z_planes):
        if "SizeZ" in file_metadatadict_for_z_planes['ImageDocument']['Metadata']['Information']['Image']:
            z_planes = int(file_metadatadict_for_z_planes['ImageDocument']['Metadata']['Information']['Image']['SizeZ'])
        else:
            z_planes = 1
        
        return(z_planes)
    
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
    
    def __init__(self, path):
        self.path = path
        
    def readczi (self):
        data = {"size_xy": None,"channel_name": None, "scaling_zxy": None, "z_planes": None, "image_array": None, "image_information": None}
        metadata = (cf.CziFile(self.path)).metadata(raw=False)
        numpy_array = cf.imread(self.path)
        data["size_xy"]=ReadImage.ImageSize_czi(metadata)
        data["channel_name"]=ReadImage.ChannelsAvaliable_czi(metadata)
        data["scaling_zxy"] =ReadImage.ImageScalingZXY_czi(metadata)
        data["z_planes"] =ReadImage.ZPlanes_czi(metadata)
        data["image_array"] =(ReadImage.ImageList_czi(numpy_array)).transpose(4,1,0,2,3)
        data["image_information"] = {"height":data["image_array"].shape[3:][0],
                                     "width":data["image_array"].shape[3:][1],
                                     "height_um":round((data["image_array"].shape[3])*(data["scaling_zxy"][1]),3),
                                     "width_um":round((data["image_array"].shape[4])*(data["scaling_zxy"][2]),3),
                                     "depth_um":round((data["image_array"].shape[1])*(data["scaling_zxy"][0]),3),
                                     "resoultion_um": round(1/(data["scaling_zxy"][2]),3)
                                     }
        return(data)
    
    
    def readnd2 (self):
        data = {"size_xy": None,"channel_name": None, "scaling_zxy": None, "z_planes": None, "image_array": None, "image_information": None}
        nd2object = AICSImage(self.path)
        metadata = nd2object.metadata
        numpy_array = nd2object.get_image_data("TZCXY")
        data["size_xy"]=nd2object.dims.X,nd2object.dims.Y
        data["channel_name"]=ReadImage.ChannelsAvaliable_nd2(metadata,nd2object.dims.C)
        data["scaling_zxy"] = nd2object.physical_pixel_sizes[0],nd2object.physical_pixel_sizes[1],nd2object.physical_pixel_sizes[2]
        data["z_planes"] = nd2object.dims.Z
        data["image_array"] =numpy_array
        data["image_information"] = {"height":data["image_array"].shape[3:][0],
                                     "width":data["image_array"].shape[3:][1],
                                      "height_um":round((data["image_array"].shape[3])*(data["scaling_zxy"][1]),3),
                                      "width_um":round((data["image_array"].shape[4])*(data["scaling_zxy"][2]),3),
                                      "depth_um":round((data["image_array"].shape[1])*(data["scaling_zxy"][0]),3),
                                      "resoultion_um": round(1/(data["scaling_zxy"][2]),3)
                                     }
        return(data)
    
    def readlif (self):
        data = {"size_xy": None,"channel_name": None, "scaling_zxy": None, "z_planes": None, "image_array": None, "image_information": None}
        lifobject = AICSImage(self.path)
        metadata = ReadImage.ElementToDict(lifobject.metadata)
        numpy_array = lifobject.get_image_data("TZCXY")
        data["size_xy"]=lifobject.dims.X,lifobject.dims.Y
        data["channel_name"]=ReadImage.ChannelsAvaliable_lif(metadata,lifobject.dims.C)
        data["scaling_zxy"] = lifobject.physical_pixel_sizes[0],lifobject.physical_pixel_sizes[1],lifobject.physical_pixel_sizes[2]
        data["z_planes"] = lifobject.dims.Z
        data["image_array"] =numpy_array
        data["image_information"] = {"height":data["image_array"].shape[3:][0],
                                     "width":data["image_array"].shape[3:][1],
                                      "height_um":round((data["image_array"].shape[3])*(data["scaling_zxy"][1]),3),
                                      "width_um":round((data["image_array"].shape[4])*(data["scaling_zxy"][2]),3),
                                      "depth_um":round((data["image_array"].shape[1])*(data["scaling_zxy"][0]),3),
                                      "resoultion_um": round(1/(data["scaling_zxy"][2]),3)
                                     }
        return (data)