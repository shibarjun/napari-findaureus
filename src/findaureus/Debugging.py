# import necessary packages
import numpy as np
from aicsimageio import AICSImage
import czifile as cf
import webcolors
import cv2

def ElementToDict(element):
    dictionary = {element.tag: {}}
    if element.attrib:
        dictionary[element.tag].update({'@' + key: value for key, value in element.attrib.items()})
    if element.text:
        dictionary[element.tag]['#text'] = element.text.strip()
    for child_element in element:
        child_dictionary = ElementToDict(child_element)
        if child_element.tag in dictionary[element.tag]:
            if isinstance(dictionary[element.tag][child_element.tag], list):
                dictionary[element.tag][child_element.tag].append(child_dictionary[child_element.tag])
            else:
                dictionary[element.tag][child_element.tag] = [dictionary[element.tag][child_element.tag], child_dictionary[child_element.tag]]
        else:
            dictionary[element.tag].update(child_dictionary)

    return dictionary

imag_path_1 = r"C:\Users\mandalshibarjun\Documents\Federike CLSM images\20230307_t00_-01(4)_example 2 (small).czi"
imag_path_2 = r"C:\Users\mandalshibarjun\Documents\Federike CLSM images\20211123_fixedt0-01(2)_example 1 (big).czi"
imag_path_3 = r"C:\Users\mandalshibarjun\Documents\171012_bone_IF12_ms59118l_G4_63x_NDD_z-stack60um_tile4x4_highres.czi"
# numpy_array = cf.imread(imag_path_3)
# czi = cf.CziFile(imag_path_1)
# array_data = czi.asarray()

img2obejct = AICSImage(imag_path_1)
image_reader = img2obejct.reader
image_data = image_reader.data
image_channel_names = image_reader.channel_names
img_metadata = img2obejct.metadata
img_metadata_dict = ElementToDict(img_metadata)
