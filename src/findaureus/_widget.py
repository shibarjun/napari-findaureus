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
from qtpy.QtCore import Qt
from qtpy.QtGui import QFont

class Find_Bacteria(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.init_ui()
        self.viewer.layers.selection.events.active.connect(self.on_layer_selection_change)

    def init_ui(self):
        layout = QVBoxLayout()

        buttonfont = QFont("Arial", 10)
        labelfont = QFont("Arial", 10)
        
        fb_button = QPushButton("Find bacteria!")
        fb_button.clicked.connect(self.FindBacteria)
        fb_button.setFont(buttonfont)
        layout.addWidget(fb_button)
        
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_viewer_and_widget)
        reset_button.setFont(buttonfont)
        layout.addWidget(reset_button, alignment=Qt.AlignHCenter)
        
        instruction_button = QPushButton("Instruction")
        instruction_button.clicked.connect(self.instruction_button)
        instruction_button.setFont(buttonfont)
        layout.addWidget(instruction_button, alignment=Qt.AlignRight)
        
        self.image_processed = QLabel("")
        self.image_processed.setFont(labelfont)
        layout.addWidget(self.image_processed)
        
        self.Channel_label= QLabel("Channel selected: ")
        self.Channel_label.setFont(labelfont)
        layout.addWidget(self.Channel_label)
        
        self.bacteria_info_label1 = QLabel("")
        self.bacteria_info_label1.setFont(labelfont)
        layout.addWidget(self.bacteria_info_label1)
        
        self.bacteria_info_label2 = QLabel("")
        self.bacteria_info_label2.setFont(labelfont)
        layout.addWidget(self.bacteria_info_label2)
        
        

        self.setLayout(layout)
        
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
            bac_data_bb = Find_Bacteria.for_napari(bac_image_list)
            self.bac_dict = bac_centroid_xy_coordinates
            print("Findbac Done")
            self.image_processed.setText("Image processed and added as a new layer.")
            self.bacteria_info_label1.setText(f"No. of Channel with Bacteria:.{len(bac_centroid_xy_coordinates)} \nNo. of Channel without Bacteria: {len(no_bac_dict)} ")
            if scalez==1:
                bac_found = len(bac_centroid_xy_coordinates["xy_Z_0"])
                self.bacteria_info_label2.setText(f"No. of Bacterial Region: {bac_found}")
            else:
                self.viewer.dims.events.current_step.connect(self.on_active_layer_change)
            self.viewer.add_image(bac_data_bb, name=f"{current_layer.name}_Bounding box", scale= scalezxy, opacity=0.7)
            self.viewer.add_image(bac_data_mask, name=f"{current_layer.name}_Bacteria mask", scale= scalezxy, opacity=0.5, colormap='red')
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
        active_layer = event.value
        
        try:
            layer_name, layer_height_um, layer_height_px, layer_width_um, layer_width_px, depth_um,scalex = Find_Bacteria.for_raw_layer(active_layer)
            
            self.Channel_label.setText(f"Channel selected: {layer_name} \nImage height: {layer_height_um} microns ({layer_height_px}) \nImage width: {layer_width_um} microns ({layer_width_px}) \nImage depth: {depth_um} microns \nImage resolution: {round(1/scalex)} pixels per micron")
        except:
            
            self.Channel_label.setText("No active layer selected.")
            
    
    def on_active_layer_change(self):
        
        try:
            current_z_plane = int(self.viewer.dims.current_step[2])# Index 2 corresponds to the new layer Z-plane value
        except:
            current_z_plane = 0
        bacteria_dic = self.bac_dict
        if "xy_Z_"+format(current_z_plane) in bacteria_dic:
            bac_found = len(bacteria_dic["xy_Z_"+format(current_z_plane)])
            self.bacteria_info_label2.setText(f"No. of Bacterial Region: {bac_found}")
        else:
            self.bacteria_info_label2.setText("No. of Bacterial Region: N/A")
    
    def reset_viewer_and_widget(self):
        self.viewer.layers.select_all()
        self.viewer.layers.remove_selected()
        self.clear_texts_and_labels()
        
    def clear_texts_and_labels(self):
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            # if isinstance(widget, QLabel)and widget is not self.welcome_label:
            if isinstance(widget, QLabel):
                widget.setText('')
                
    def instruction_button(self):
        self.instruction_window = InstructionWindow()
        self.instruction_window.show()
        
class InstructionWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Instruction")
        self.setGeometry(200, 200, 500, 500)

        layout = QVBoxLayout()
        labelfont = QFont("Arial", 10)

        self.label = QLabel("Welcome to Napari-Findaureus Widget\n\nStep 1: Load Your Fluorescence Image File\nSupported formats are Zeiss (.czi), Leica (.lif), and Nikon (.nd2)\nUse ""Open with Plugin"" option to load your fluorescence image file.\n\nStep 2 :Explore the Loaded Image Using the Napari Viewer\nFind the relevant image information in the widget\n\nStep 3: Choose the Image Channel/Layer to Locate Bacteria\n\nStep 4: Locate Bacteria\nPress the ""Find Bacteria"" button Provided in the napari-Findaureus widget\nTwo new layers will be added to the viewer:\n- Bacteria mask: Shows the identified bacteria in the selected channel.\n- Bounding boxes: Indicates the bounding boxes around the detected bacteria.\n\nStep 5: Explore All Napari Features\nTake advantage of all the features supported by Napari to view/analyze your image.\n\nStep 6: Reset the Viewer\nBefore importing a new image file, reset the viewer to start fresh.\nYou can use the ""Reset"" button provided in the widget, or simply restart the viewer.", self)
        self.label.setFont(labelfont)
        layout.addWidget(self.label)

        self.setLayout(layout)