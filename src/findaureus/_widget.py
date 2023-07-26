"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
import numpy as np
from typing import TYPE_CHECKING
from .Module_Class import ReadImage
import napari.layers

if TYPE_CHECKING:
    import napari

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

class Find_Bacteria(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.init_ui()
        # self.current_z_plane_integer = None
        # self.viewer.dims.events.current_step.connect(self.on_active_layer_change)

    def init_ui(self):
        layout = QVBoxLayout()

        self.welcome_label = QLabel("Hello, welcome to the widget Findaureus \n Please select the channel!")
        layout.addWidget(self.welcome_label)

        button = QPushButton("Find bacteria!")
        button.clicked.connect(self.FindBacteria)
        layout.addWidget(button)
        
        self.Channel_label= QLabel("Channel selected: ")
        layout.addWidget(self.Channel_label)
        
        self.bacteria_info_label1 = QLabel("")
        layout.addWidget(self.bacteria_info_label1)
        
        self.bacteria_info_label2 = QLabel("")
        layout.addWidget(self.bacteria_info_label2)

        self.setLayout(layout)
        
        
        self.viewer.layers.selection.events.active.connect(self.on_layer_selection_change)
        self.viewer.dims.events.current_step.connect(self.on_active_layer_change)
        
    def for_napari(image_list):
        data =np.stack(image_list)
        data = np.expand_dims(data, -1)
        data = data.transpose(3,0,1,2)
        data = np.expand_dims(data, axis=0)
        return(data)


    def FindBacteria(self)-> "napari.types.LayerDataTuple":
        current_layer = self.viewer.layers.selection.active
        if current_layer is not None:
            
            image_list = list(current_layer.data[0,:,:,:])
            _,scalez,scalex ,scaley  = current_layer.scale 
            scalexy = (scalex,scaley)
            scalezxy = (scalez,scaley,scalex)
            bac_image_list,bac_image_list_mask, bac_centroid_xy_coordinates, no_bac_dict, bac_pixelwise_xy_coordinates, bacteria_area = ReadImage.FindBacteriaAndNoBacteria(image_list, scalexy)
            bac_data_mask = Find_Bacteria.for_napari(bac_image_list_mask)
            self.bac_dict = bac_centroid_xy_coordinates
            print("Findbac Done")
            self.welcome_label.setText("Image processed and added as a new layer.")
            self.bacteria_info_label1.setText(f"No. of Channel with Bacteria:.{len(bac_image_list)} \nNo. of Channel without Bacteria: {len(no_bac_dict)} ")
            self.viewer.add_image(bac_data_mask, name=f"{current_layer.name}_Bacteria mask", scale= scalezxy, opacity=0.5, colormap='red')
            # self.on_active_layer_change()
            
            # z_plane_value = self.current_z_plane_integer
            # print(z_plane_value)
            # self.viewer.dims.events.current_step.connect(self.on_active_layer_change)
        else:
            self.welcome_label.setText("No active layer selected.")
        
    def for_raw_layer(active_layer):
        
        _,scalez,scalex ,scaley  = active_layer.scale
        layer_name = active_layer.name
        layer_shape = active_layer.data.shape
        z_layer, layer_height_px, layer_width_px = layer_shape[1],layer_shape[2],layer_shape[3]
        depth_um, layer_height_um, layer_width_um = z_layer*scalez, layer_height_px*scalex, layer_width_px*scaley
        return(layer_name, layer_height_um, layer_height_px, layer_width_um, layer_width_px, depth_um,scalex)
    
    def on_layer_selection_change(self, event):
        # Function to update the text on layer selection change
        active_layer = event.value
        # current_layer = self.viewer.layers.selection.active
        
        try:
            # Update the text with information about the selected layer
            layer_name, layer_height_um, layer_height_px, layer_width_um, layer_width_px, depth_um,scalex = Find_Bacteria.for_raw_layer(active_layer)
            
            self.Channel_label.setText(f"Channel selected: {layer_name} \nImage height: {layer_height_um} microns ({layer_height_px}) \nImage width: {layer_width_um} microns ({layer_width_px}) \nImage depth: {depth_um} microns \nImage resolution: {round(1/scalex)} pixels per micron")
        except:
            
            self.Channel_label.setText("No active layer selected.")
            
    
    def on_active_layer_change(self):
        current_z_plane = int(self.viewer.dims.current_step[2])# Index 2 corresponds to the new layer Z-plane value
        bacteria_dic = self.bac_dict
        
        self.bacteria_info_label2.setText(f"No. of Bacterial Region: {current_z_plane}")
        