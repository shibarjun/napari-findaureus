import numpy as np
from aicsimageio import AICSImage
import czifile as cf
import webcolors
import cv2
import torch
import os
from .Segment_Boxes import segment_and_get_bounding_boxes
import xmltodict

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
    
    def ElementToDict(t):
        d = {t.tag: {} if t.attrib else None}
        children = list(t)
        if children:
            dd = {}
            for dc in map(ReadImage.ElementToDict, children):
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
    
    def ImageSize_czi (file_metadatadict_for_imagesize):
        image_size_x = int(file_metadatadict_for_imagesize['ImageDocument']['Metadata']['Information']['Image']['SizeX'])
        image_size_y = int(file_metadatadict_for_imagesize['ImageDocument']['Metadata']['Information']['Image']['SizeY'])
        return(image_size_x, image_size_y)
    
    def ChannelsAvaliable_czi(file_metadatadict_for_channel):
        channel_names = []
        channel_colours = []
        channel_colours_name = []
        channel_size = int(file_metadatadict_for_channel['ImageDocument']['Metadata']['Information']['Image']['SizeC'])
        
        if channel_size == 1:
            channel_names.append(file_metadatadict_for_channel['ImageDocument']['Metadata']['DisplaySetting']['Channels']['Channel']['Name'])
            channel_colours.append(file_metadatadict_for_channel['ImageDocument']['Metadata']['DisplaySetting']['Channels']['Channel']['Color'])
        if channel_size > 1:
            for ch in range(channel_size):
                channel_names.append(file_metadatadict_for_channel['ImageDocument']['Metadata']['DisplaySetting']['Channels']['Channel'][ch]['Name'])
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
        
        return(channel_names, channel_colours_name)
    
    def ChannelsAvaliable_nd2 (image_metadata,channel_size):
        channel_names = []
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
        if channel_names==[]:
            channel_names = channel_colours
        return (channel_names,channel_colours_name)
    
    def ChannelsAvaliable_lif (image_metadata,channel_size):
        channel_names = []
        channel_colours_name = []
        if channel_size == 1:
            channel_colours_name.append(image_metadata['LMSDataContainerHeader']['Element']['Children']['Element'][0]['Data']['Image']["ImageDescription"]["Channels"]["ChannelDescription"]["@LUTName"])
        if channel_size > 1:
            for ch in range(channel_size):
                channel_colours_name.append(image_metadata['LMSDataContainerHeader']['Element']['Children']['Element'][0]['Data']['Image']["ImageDescription"]["Channels"]["ChannelDescription"][ch]["@LUTName"])
        if channel_names==[]:
            channel_names = channel_colours_name
        return(channel_names, channel_colours_name)
    
    def ChannelsAvaliable_tiff (image_metadata,channel_size):
        channel_names = []
        channel_colours = []
        if channel_size == 1:
            pass
        if channel_size > 1:
            for ch in range(channel_size):
                channel_names.append(image_metadata['OME']['Image']['Pixels']['Channel'][ch]['@Name'])
                channel_colour = image_metadata['OME']['Image']['Pixels']['Channel'][ch]['@Color']
                try:
                    channel_colour = int(channel_colour)
                    rgb_color = (channel_colour >> 16 & 255, channel_colour >> 8 & 255, channel_colour & 255)
                    color_name = webcolors.rgb_to_name(rgb_color)
                except ValueError:
                    color_name = "mixed"
                channel_colours.append(color_name)
        return(channel_names, channel_colours)
    
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
    
    def ImageScalingZXY_tiff (file_metadatadict_for_scaling):
        scale_x =  float(file_metadatadict_for_scaling['OME']['Image']['Pixels']["@PhysicalSizeX"])
        scale_y =  float(file_metadatadict_for_scaling['OME']['Image']['Pixels']["@PhysicalSizeY"])
        scale_z =  float(file_metadatadict_for_scaling['OME']['Image']['Pixels']["@PhysicalSizeZ"])
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
        data["channel_name"]=ReadImage.ChannelsAvaliable_czi(img_metadata)[0]
        data["channel_colors"]=ReadImage.ChannelsAvaliable_czi(img_metadata)[1]
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
        data["channel_name"]=ReadImage.ChannelsAvaliable_nd2(img_metadata,nd2object.dims.C)[0]
        data["channel_colors"]=ReadImage.ChannelsAvaliable_nd2(img_metadata,nd2object.dims.C)[1]
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
        data["channel_name"]=ReadImage.ChannelsAvaliable_lif(img_metadata,lifobject.dims.C)[0]
        data["channel_colors"]=ReadImage.ChannelsAvaliable_lif(img_metadata,lifobject.dims.C)[1]
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
    
    def readtiff (self):
        data = {"size_xy": None,"channel_name": None, "scaling_zxy": None, "z_planes": None, "image_array": None, "image_information": None}
        tiffobject = AICSImage(self.path)
        img_metadata = tiffobject.metadata
        img_metadata = str(img_metadata)
        img_metadata = xmltodict.parse(img_metadata)
        numpy_array = tiffobject.get_image_data("TZCXY")
        data["size_xy"]=tiffobject.dims.X,tiffobject.dims.Y
        data["channel_name"]=ReadImage.ChannelsAvaliable_tiff(img_metadata,tiffobject.dims.C)[0]
        data["channel_colors"]=ReadImage.ChannelsAvaliable_tiff(img_metadata,tiffobject.dims.C)[1]
        data["scaling_zxy"] = ReadImage.ImageScalingZXY_tiff(img_metadata)
        data["z_planes"] = tiffobject.dims.Z
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

    # Statistical detection helpers removed — module now uses CNN-only pipeline
    
    def FindBacteriaAndNoBacteria(imagelist, scalexy, model_path=None, model=None, input_shape=(25,25), min_probability=0.30, device=None, batch_size=32):
        """
        Find bacteria using a CNN classifier applied to candidate regions produced by segmentation.
        If `model` or `model_path` is provided the CNN pipeline is used. Otherwise falls back to
        the original threshold/morphology-based method.

        Parameters:
        - imagelist: list of 2D numpy arrays (one per z-plane)
        - scalexy: tuple (scale_x, scale_y) in microns per pixel
        - model_path: optional path to a torch saved state_dict or model
        - model: optional already-constructed torch model
        - input_shape: (width, height) for CNN input
        - min_probability: threshold for positive detections
        - device: torch device string or torch.device
        - batch_size: inference batch size
        - (NMS removed) IoU threshold parameter removed; all boxes above `min_probability` are kept

        Returns same tuple as previous implementation, plus bacteria_probability scores.
        """
        bac_image_list_mask = []
        bac_image_list = []
        no_bac_image_list = []
        no_bac_image_name_list = []
        bac_pixelwise_xy_coordinates = {}
        bac_centroid_xy_coordinates = {}
        bacteria_area = {}
        bacteria_probability = {}

        # setup device
        if device is None:
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        elif isinstance(device, str):
            device = torch.device(device)

        # default model path to packaged model in this package
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), 'BacteriaClassifier_ConvNetSimple.pt')

        # load model
        loaded_model = None
        if model is not None:
            loaded_model = model.to(device)
            loaded_model.eval()
        else:
            try:
                loaded_data = torch.load(model_path, map_location=device)
                try:
                    from .model_architecture import ConvNetSimple
                    if isinstance(loaded_data, dict) and 'state_dict' in loaded_data:
                        loaded_model = ConvNetSimple().to(device)
                        loaded_model.load_state_dict(loaded_data['state_dict'])
                    else:
                        loaded_model = ConvNetSimple().to(device)
                        loaded_model.load_state_dict(loaded_data)
                except Exception:
                    # try using loaded object directly (scripted model or saved module)
                    if hasattr(loaded_data, 'eval'):
                        loaded_model = loaded_data
                    elif isinstance(loaded_data, dict) and 'model' in loaded_data:
                        loaded_model = loaded_data['model']
                if loaded_model is not None and hasattr(loaded_model, 'to'):
                    loaded_model = loaded_model.to(device)
                if hasattr(loaded_model, 'eval'):
                    loaded_model.eval()
                print(f"[findaureus] CNN model loaded from: {model_path}  (device={device})")
            except Exception as e:
                raise FileNotFoundError(f'Failed to load CNN model from {model_path}: {e}')

        print(f"[findaureus] Starting CNN detection on {len(imagelist)} z-planes")
        for imageno in range(0, len(imagelist)):
            input_image = imagelist[imageno]

            # CNN-only pipeline (statistical helpers removed)

            # CNN path: get candidate boxes from segmentation helper
            rectangles_sb, imagewithbox, segmentation_mask = segment_and_get_bounding_boxes(input_image)
            print(f"[findaureus] z={imageno}: segmentation returned {len(rectangles_sb)} candidate boxes")
            if len(rectangles_sb) == 0:
                no_bac_image_list.append(input_image)
                no_bac_image_name_list.append('z'+str(imageno))
                # append empty mask and image for consistency
                bac_image_list_mask.append(np.zeros_like(input_image))
                bac_image_list.append(np.zeros_like(input_image))
                bac_pixelwise_xy_coordinates["p_xy_"+format(imageno)] = []
                continue

            roi_tensors = []
            roi_positions = []
            for (x, y, w, h) in rectangles_sb:
                roi = input_image[y:y + h, x:x + w]
                if roi.size == 0:
                    continue
                resized_image = cv2.resize(roi, input_shape)
                preprocessed_image = resized_image.astype(np.float32) / 255.0
                roi_tensor = torch.tensor(preprocessed_image, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
                roi_tensors.append(roi_tensor)
                roi_positions.append((x, y, x + w, y + h))

            if not roi_tensors:
                no_bac_image_list.append(input_image)
                no_bac_image_name_list.append('z'+str(imageno))
                bac_image_list_mask.append(np.zeros_like(input_image))
                bac_image_list.append(np.zeros_like(input_image))
                bac_pixelwise_xy_coordinates["p_xy_"+format(imageno)] = []
                continue
            batch_tensor = torch.cat(roi_tensors, dim=0).to(device)
            print(f"[findaureus] z={imageno}: running CNN inference on {batch_tensor.shape[0]} ROIs (batch_size={batch_size})")
            num_rois = batch_tensor.shape[0]
            all_probs = []
            with torch.no_grad():
                for i in range(0, num_rois, batch_size):
                    mini = batch_tensor[i:i+batch_size]
                    out = loaded_model(mini)
                    out_np = out.cpu().numpy()
                    # normalize outputs to probabilities
                    if out_np.ndim == 2 and out_np.shape[1] == 2:
                        # softmax and take class 1
                        exp = np.exp(out_np - out_np.max(axis=1, keepdims=True))
                        probs = exp[:,1] / exp.sum(axis=1)
                    else:
                        probs = out_np.flatten()
                        if probs.min() < 0 or probs.max() > 1:
                            probs = 1.0/(1.0 + np.exp(-probs))
                    all_probs.append(probs)

            all_probs = np.concatenate(all_probs, axis=0)
            print(f"[findaureus] z={imageno}: inference produced {all_probs.shape[0]} probability scores")

            # filter by threshold
            rois = []
            boxes = []
            scores = []
            for i, p in enumerate(all_probs):
                if p > min_probability:
                    x1, y1, x2, y2 = roi_positions[i]
                    boxes.append([x1, y1, x2, y2])
                    scores.append(p)
            print(f"[findaureus] z={imageno}: {len(boxes)} ROIs above threshold {min_probability}")

            kept_indices = []
            if boxes:
                # keep all boxes above threshold (no NMS)
                boxes = np.array(boxes)
                scores = np.array(scores)
                kept_indices = list(range(len(boxes)))
                print(f"[findaureus] z={imageno}: {len(kept_indices)} boxes kept (no NMS applied)")

            # build output images / masks
            bound_boxed_image = np.zeros_like(input_image)
            centroid = []
            coord_area_um2 = {}
            coord_prob = {}
            for idx in kept_indices:
                x1, y1, x2, y2 = boxes[idx]
                x1i, y1i, x2i, y2i = int(x1), int(y1), int(x2), int(y2)
                
                # Draw rectangle on the bounding box image
                cv2.rectangle(bound_boxed_image, (x1i, y1i), (x2i, y2i), 255, 1)
                
                # Add probability text above the box
                confidence = scores[idx]
                text = f'{confidence*100:.1f}%'
                # Get text size for better positioning
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
                text_x = max(0, x1i)
                text_y = max(text_size[1] + 2, y1i - 2)
                cv2.putText(bound_boxed_image, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, 255, 1, cv2.LINE_AA)
                
                w = x2i - x1i
                h = y2i - y1i
                cx = int(x1i + 0.5 * w)
                cy = int(y1i + 0.5 * h)
                centroid.append((cx, cy))
                # approximate area in um^2
                contour_area_um = (scalexy[0] * scalexy[1]) * (w * h)
                coord_area_um2[(cx, cy)] = contour_area_um
                # store probability score
                coord_prob[(cx, cy)] = float(confidence)

            if centroid == []:
                no_bac_image_list.append(bound_boxed_image)
                no_bac_image_name_list.append('z'+str(imageno))
            else:
                bac_image_list.append(bound_boxed_image)
                bac_centroid_xy_coordinates["xy_Z_"+format(imageno)] = centroid
                bacteria_area["xy_Z_"+format(imageno)] = coord_area_um2
                bacteria_probability["xy_Z_"+format(imageno)] = coord_prob
                bac_pixelwise_xy_coordinates["p_xy_"+format(imageno)] = []
                # Build a bacteria-shaped mask by copying the segmentation mask
                final_mask = np.zeros_like(input_image, dtype=np.uint8)
                try:
                    box_sizes = []
                    for idx in kept_indices:
                        x1, y1, x2, y2 = boxes[idx]
                        x1i, y1i, x2i, y2i = int(x1), int(y1), int(x2), int(y2)
                        # copy the segmentation-derived filled contours within the box region
                        roi_mask = segmentation_mask[y1i:y2i, x1i:x2i]
                        if roi_mask.size:
                            final_mask[y1i:y2i, x1i:x2i] = np.maximum(final_mask[y1i:y2i, x1i:x2i], roi_mask)
                            box_sizes.append(max(1, x2i-x1i, y2i-y1i))

                    # Ensure binary 0/255
                    final_mask = (final_mask > 0).astype(np.uint8) * 255

                    # If we have box sizes, choose a kernel proportional to average box size
                    if box_sizes:
                        avg_box = int(max(3, np.mean(box_sizes)))
                        # kernel smaller than box but large enough to fill interior gaps
                        k = max(3, int(max(3, avg_box // 6)))
                        if k % 2 == 0:
                            k += 1
                    else:
                        k = 7

                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
                    # Close small holes and gaps, then dilate slightly to join fragments
                    final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
                    final_mask = cv2.dilate(final_mask, kernel, iterations=1)

                    # If mask is still very sparse compared to union of boxes, fill boxes as fallback
                    mask_pixels = np.count_nonzero(final_mask)
                    union_box_area = 0
                    for idx in kept_indices:
                        x1, y1, x2, y2 = boxes[idx]
                        union_box_area += max(0, int(x2 - x1)) * max(0, int(y2 - y1))

                    if union_box_area > 0 and mask_pixels < 0.15 * union_box_area:
                        for idx in kept_indices:
                            x1, y1, x2, y2 = boxes[idx]
                            x1i, y1i, x2i, y2i = int(x1), int(y1), int(x2), int(y2)
                            final_mask[y1i:y2i, x1i:x2i] = 255

                except Exception:
                    # Fallback to bounding-box representation if something goes wrong
                    final_mask = (bound_boxed_image > 0).astype(np.uint8) * 255

                bac_image_list_mask.append(final_mask)

        no_bac_dict = dict(zip(no_bac_image_name_list, no_bac_image_list))
        return (bac_image_list, bac_image_list_mask, bac_centroid_xy_coordinates, no_bac_dict, bac_pixelwise_xy_coordinates, bacteria_area, bacteria_probability)