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
        self.viewer.layers.selection.events.active.connect(self.on_layer_selection_change)

    def init_ui(self):
        layout = QVBoxLayout()

        self.label1 = QLabel("Hello, welcome to the widget Findaureus \n Please select the channel!")
        layout.addWidget(self.label1)

        button = QPushButton("Find bacteria!")
        button.clicked.connect(self.FindBacteria)
        layout.addWidget(button)
        self.label2 = QLabel("Channel selected: ")
        layout.addWidget(self.label2)
        
        self.label3 = QLabel("No of channel with bacteria: \nNo of channel without bacteria:")
        layout.addWidget(self.label3)

        self.setLayout(layout)
    #     self.update_layer_combo()
    
    # def get_layer_names(self):
    #     # Function to get a list of layer names in a thread-safe manner.
    #     return [layer.name for layer in self.viewer.layers]
    
    # def update_layer_combo(self):
    #     # Update the combobox with the available layer names.
    #     layer_names = self.get_layer_names()
    #     self.layer_combo.clear()
    #     self.layer_combo.addItems(layer_names)

    # def on_button_click(self):
    #     # Example action to perform when the button is clicked
    #     # layout = QVBoxLayout()
    #     current_layer = self.viewer.layers.selection.active
        
    #     if current_layer is not None:
    #         self.label.setText(f"Channel selected: {current_layer.name}")
    #         print(f"Active layer name: {current_layer.name}")
    #     else:
    #         print("No active layer selected.")



# class ExampleQWidget(QWidget):
#     # your QWidget.__init__ can optionally request the napari viewer instance
#     # in one of two ways:
#     # 1. use a parameter called `napari_viewer`, as done here
#     # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
#     def __init__(self, napari_viewer):
#         super().__init__()
#         self.viewer = napari_viewer

#         btn = QPushButton("Click me!")
#         btn.clicked.connect(self._on_click)

#         self.setLayout(QHBoxLayout())
#         self.layout().addWidget(btn)

#     def _on_click(self):
#         print("napari has", len(self.viewer.layers), "layers")
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
            # z_value, x_value, y_value = ReadImage.ImageScalingXY
            # bac_data_box = Find_Bacteria.for_napari(bac_image_list)
            bac_data_mask = Find_Bacteria.for_napari(bac_image_list_mask)
            # bac_data = np.concatenate ((bac_data_box,bac_data_mask), axis = 2)
            # bac_layer = (bac_data, {"scale": scalezxy,"name": (f"{img_layer.name}_Bbox", f"{img_layer.name}_mask")})
            # bac_layer = (bac_data_mask, {"scale": scalezxy,"name": f"{current_layer.name}_Bbox", "opacity":0.5})
            print("Findbac Done")
            self.label1.setText("Image processed and added as a new layer.")
            self.label3.setText(f"No of channel with bacteria:.{len(bac_image_list)} \nNo of channel without bacteria: {len(no_bac_dict)}")
            self.viewer.add_image(bac_data_mask, name=f"{current_layer.name}_Bacteria mask", scale= scalezxy, opacity=0.5, colormap='red')
        else:
            self.label1.setText("No active layer selected.")
        # return [bac_layer]
        
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
            
            self.label2.setText(f"Channel selected: {layer_name} \nImage height: {layer_height_um} microns ({layer_height_px}) \nImage width: {layer_width_um} microns ({layer_width_px}) \nImage depth: {depth_um} microns \nImage resolution: {round(1/scalex)} pixels per micron")
        except:
            
            self.label2.setText("No active layer selected.")



# Uses the `autogenerate: true` flag in the plugin manifest
# to indicate it should be wrapped as a magicgui to autogenerate
# a widget.
# def example_function_widget(img_layer: "napari.layers.Image"):
#     print(f"you have selected {img_layer}")
