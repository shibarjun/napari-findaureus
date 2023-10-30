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
    
    def __init__(self, path, data=None):
        self.path = path
        self.data = data
        
    def readczi (self):
        data = {"size_xy": None,"channel_name": None, "scaling_zxy": None, "z_planes": None, "image_array": None, "image_information": None}
        img_metadata = (cf.CziFile(self.path)).metadata(raw=False)
        numpy_array = cf.imread(self.path)
        data["size_xy"]=ReadImage.ImageSize_czi(img_metadata)
        data["channel_name"]=ReadImage.ChannelsAvaliable_czi(img_metadata)
        data["scaling_zxy"] =tuple(ReadImage.ImageScalingZXY_czi(img_metadata))
        data["z_planes"] =ReadImage.ZPlanes_czi(img_metadata)
        data["image_array"] =(ReadImage.ImageList_czi(numpy_array)).transpose(4,1,0,2,3)
        data["image_information"] = {"height":data["image_array"].shape[3:][0],
                                     "width":data["image_array"].shape[3:][1],
                                     "height_um":round((data["image_array"].shape[3])*(data["scaling_zxy"][1]),3),
                                     "width_um":round((data["image_array"].shape[4])*(data["scaling_zxy"][2]),3),
                                     "depth_um":round((data["image_array"].shape[1])*(data["scaling_zxy"][0]),3),
                                     "resoultion_um": round(1/(data["scaling_zxy"][2]),3)
                                     }
        self.data=data
        return(data)
    
    
    def readnd2 (self):
        data = {"size_xy": None,"channel_name": None, "scaling_zxy": None, "z_planes": None, "image_array": None, "image_information": None}
        nd2object = AICSImage(self.path)
        img_metadata = nd2object.metadata
        numpy_array = nd2object.get_image_data("TZCXY")
        data["size_xy"]=nd2object.dims.X,nd2object.dims.Y
        data["channel_name"]=ReadImage.ChannelsAvaliable_nd2(img_metadata,nd2object.dims.C)
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
        self.data=data
        return(data)
    
    def readlif (self):
        data = {"size_xy": None,"channel_name": None, "scaling_zxy": None, "z_planes": None, "image_array": None, "image_information": None}
        lifobject = AICSImage(self.path)
        img_metadata = ReadImage.ElementToDict(lifobject.metadata)
        numpy_array = lifobject.get_image_data("TZCXY")
        data["size_xy"]=lifobject.dims.X,lifobject.dims.Y
        data["channel_name"]=ReadImage.ChannelsAvaliable_lif(img_metadata,lifobject.dims.C)
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
        self.data=data
        return (data)

    def CreateBacteriaMask(input_image):
        upper = int(np.max(input_image))
        try:
            lower = -np.log(0.001)*np.median(input_image) / np.log(2)
        except ZeroDivisionError:
            lower=()
        bacteria_mask = cv2.inRange(input_image, lower, upper)
        
        return(bacteria_mask, lower)
    
    def MorphologicalOperations(bacteria_mask):
        kernel = np.ones((3,3),np.uint8)
        opening_bacteria_mask = cv2.morphologyEx(bacteria_mask, cv2.MORPH_OPEN, kernel)
        numLabels, labeled_image = cv2.connectedComponents(opening_bacteria_mask)
        labeled_image = np.uint8(labeled_image)
        morphed_image = cv2.medianBlur(labeled_image,5)
        
        return(morphed_image)
    
    def FindingContours(input_morphed_image):
        contours, hierarchy = cv2.findContours(input_morphed_image, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        return(contours)
    
    def GetPixelWiseBacteriaCoordinates(input_morphed_image):
        bac_pixel_coords = np.argwhere(input_morphed_image)
        xy_pixelwise_coords = []
        for p in bac_pixel_coords:
            pxy = p[0], p[1]
            xy_pixelwise_coords.append(pxy)
        
        return(xy_pixelwise_coords)
    
    def NonMaxSuppression(boxes, overlap_thresh):
        if len(boxes) == 0:
            return []

        if isinstance(boxes, list):
            boxes = np.array(boxes)
        pick = []
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 0] + boxes[:, 2]
        y2 = boxes[:, 1] + boxes[:, 3]
        area = boxes[:, 2] * boxes[:, 3]
        idxs = np.argsort(y2)


        while len(idxs) > 0:

            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)

            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])


            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)


            overlap = (w * h) / area[idxs[:last]]


            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))


        return boxes[pick]
    
    def MakeBoundingBoxWithCentroid(input_image, found_contour,scalexy):
        centroid = []
        area_list_um2 = []
        boxes = []
        bound_boxed_image = input_image.copy()
        
        
        for cnt in found_contour:
            # try:
            #     scalez,scalex,scaley = scalezxy
            # except:
            scalex,scaley =scalexy
                
            bac_dia = 0.5 # considering bac size 0.5 um in diameter
            contour_area = cv2.contourArea(cnt)
            contour_area_um = (scalex*scaley)*(contour_area)
            area_bac_um = np.pi*(bac_dia/2)**2
            
            if contour_area_um<=area_bac_um: 
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            
            if w and h >= input_image.shape[0] and input_image.shape[1]:
                break
            boxes.append((x,y,w,h))
       
        selected_boxes = ReadImage.NonMaxSuppression(boxes, overlap_thresh=0.3)
            
        for box in selected_boxes:
            x,y,w,h = box
            cv2.rectangle(bound_boxed_image,(x,y),(x+w,y+h),(255,0,0),1)
            cx = int(x + 0.5 * w)
            cy = int(y + 0.5 * h)
            cxy = (cx,cy)
            area_list_um2.append(contour_area_um)
            centroid.append(cxy)
        
        coord_area_um2 = dict(zip(centroid,area_list_um2))
        
        return(bound_boxed_image, centroid, coord_area_um2)
    
    def FindBacteriaAndNoBacteria(imagelist, scalexy):
        bac_image_list_mask = []
        bac_image_list = []
        no_bac_image_list = []
        no_bac_image_name_list = []
        bac_pixelwise_xy_coordinates = {}
        bac_centroid_xy_coordinates = {}
        bacteria_area = {}
        for imageno in range(0,len(imagelist)):
            locals()["xy_Z_"+format(imageno)] = []
            locals()["p_xy_"+format(imageno)] = []
            input_image = imagelist[imageno]
            mask_image, maskvalue_lower = ReadImage.CreateBacteriaMask(input_image)
            if maskvalue_lower == ():
                no_bac_image_list.append(input_image)
                no_bac_image_name_list.append('z'+str(imageno))
                continue
            morph_image = ReadImage.MorphologicalOperations(mask_image)
            morph_image[morph_image>0]=255
            bac_image_list_mask.append(morph_image)
            contours_avaliable = ReadImage.FindingContours(morph_image)
            bac_pixel_coordinates = ReadImage.GetPixelWiseBacteriaCoordinates(morph_image)
            locals()["p_xy_"+format(imageno)].append(bac_pixel_coordinates)
            bac_pixelwise_xy_coordinates["p_xy_"+format(imageno)]=bac_pixel_coordinates
            
            bac_image,bac_centroid_coordinates,bact_area = ReadImage.MakeBoundingBoxWithCentroid(input_image, contours_avaliable,scalexy)
            bac_image_list.append(bac_image)
            if bac_centroid_coordinates == []:
                no_bac_image_list.append(bac_image)
                no_bac_image_name_list.append('z'+str(imageno))
            else:
                
                locals()["xy_Z_"+format(imageno)].append(bac_centroid_coordinates)
                bac_centroid_xy_coordinates["xy_Z_"+format(imageno)]= bac_centroid_coordinates
                bacteria_area["xy_Z_"+format(imageno)]=bact_area
        no_bac_dict = dict(zip(no_bac_image_name_list, no_bac_image_list))
        
        return(bac_image_list,bac_image_list_mask, bac_centroid_xy_coordinates, no_bac_dict, bac_pixelwise_xy_coordinates, bacteria_area)