"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/stable/plugins/guides.html?#widgets

Replace code below according to your needs.
"""
from typing import TYPE_CHECKING
from .Module_Class import *
import napari.layers

if TYPE_CHECKING:
    import napari

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit, QHBoxLayout, QTextEdit
from qtpy.QtCore import Qt, QUrl
from qtpy.QtGui import QFont, QPixmap, QCursor, QDesktopServices

def open_url():
    QDesktopServices.openUrl(QUrl("https://github.com/shibarjun/napari_findaureus-v1"))

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
        
        # title
        self.title = QLabel("<h1>Findaureus</h1>")
        self.title.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.title, alignment=Qt.AlignCenter)
        
        #banner content
        content_widget_1 = QWidget()
        content_layout_1 = QHBoxLayout(content_widget_1)
        
        ##findauresu icon
        icon_fa = QPixmap("src/findaureus/resources/application_icon.png")
        icon_fa = icon_fa.scaled(64, 64)
        fa_widget = QLabel()
        fa_widget.setPixmap(icon_fa)

        ##description
        description_widget = QPlainTextEdit()
        description_widget.setReadOnly(True)
        description_widget.setPlainText("Find bacteria in confocal laser scanning microscopy (CLSM) obtained infected bone tissue images.")
        description_widget.setFixedSize(256, 50)
        
        ##conclude the content
        content_layout_1.addWidget(fa_widget)
        content_layout_1.addWidget(description_widget)
        layout.addWidget(content_widget_1, alignment=Qt.AlignCenter)
        
        #github and instruction content
        content_widget_2 = QWidget()
        content_layout_2 = QHBoxLayout(content_widget_2)
        ##github icon
        icon_gh = QPixmap("src/findaureus/resources/GitHub-Mark-Light-32px.png")
        icon_gh = icon_gh.scaled(32,32)
        gh_widget = QLabel()
        gh_widget.setPixmap(icon_gh)
        gh_widget.setCursor(QCursor(Qt.PointingHandCursor))
        gh_widget.mouseReleaseEvent = lambda event: open_url()
        
        ##instruction
        instruction_button = QPushButton("Instruction")
        instruction_button.clicked.connect(self.open_instruction)
        instruction_button.setFont(buttonfont)
        
        ##conclude the content
        content_layout_2.addWidget(gh_widget)
        content_layout_2.addWidget(instruction_button)
        layout.addWidget(content_widget_2, alignment=Qt.AlignRight)
        
        #button to find bacteria
        fb_button = QPushButton("Find bacteria!")
        fb_button.clicked.connect(self.FindBacteria)
        fb_button.setFont(buttonfont)
        layout.addWidget(fb_button)
        
        #button to find rest the lasyer and avaliable image informations
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_viewer_and_widget)
        reset_button.setFont(buttonfont)
        layout.addWidget(reset_button, alignment=Qt.AlignRight)
        
        #text about processed information
        self.image_processed = QLabel("")
        self.image_processed.setFont(labelfont)
        layout.addWidget(self.image_processed)
        
        #text about channel selected
        self.Channel_label= QLabel("")
        self.Channel_label.setFont(labelfont)
        layout.addWidget(self.Channel_label)
        
        #text about bacteria
        self.bacteria_info_label1 = QLabel("")
        self.bacteria_info_label1.setFont(labelfont)
        layout.addWidget(self.bacteria_info_label1)
        
        #text about bacteria
        self.bacteria_info_label2 = QLabel("")
        self.bacteria_info_label2.setFont(labelfont)
        layout.addWidget(self.bacteria_info_label2)
        
        #text about layer selcted
        self.welcome_label = QLabel("")
        layout.addWidget(self.welcome_label)

        self.setLayout(layout)
        self.instruction_window = None
        
    def for_napari(image_list):
        data =np.stack(image_list)
        data = np.expand_dims(data, -1)
        data = data.transpose(3,0,1,2)
        data = np.expand_dims(data, axis=0)
        return(data)


    def FindBacteria(self)-> "napari.types.LayerDataTuple":
        current_layer = self.viewer.layers.selection.active
        self.Channel_label.setText("Channel selected: ")
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
            if isinstance(widget, QLabel)and widget is not self.welcome_label and widget is not self.title:
                widget.setText('')
        
    def open_instruction(self):
        if not self.instruction_window or not self.instruction_window.isVisible():
            self.instruction_window = QWidget()
            self.instruction_window.setWindowTitle("Instruction")

            layout = QVBoxLayout()
            
            title_in = QLabel("<h1>Instruction</h1>")
            title_in.setStyleSheet("font-weight: bold;")
            layout.addWidget(title_in)

            label = QTextEdit()
            label.setPlainText(
                "Welcome to napari-findaureus Widget\n\n"
                "Step 1: Load Your Fluorescence Image File\n"
                "Supported formats: Zeiss (.czi), Leica (.lif), and Nikon (.nd2)\n"
                "Use the 'Open with Plugin' option to load your fluorescence image file.\n\n"
                "Step 2: Explore the Loaded Image Using the Napari Viewer\n"
                "Find the relevant image information in the widget.\n\n"
                "Step 3: Choose the Image Channel/Layer to Locate Bacteria\n\n"
                "Step 4: Locate Bacteria\n"
                "Press the 'Find Bacteria' button provided in the napari-findaureus widget.\n"
                "Two new layers will be added to the viewer:\n"
                "- Bacteria mask: Highlights the identified bacteria in the selected channel.\n"
                "- Bounding boxes: Places bounding boxes around the detected bacteria.\n\n"
                "Step 5: Explore All Napari Features\n"
                "Utilize all the features supported by Napari to view and analyze your image.\n\n"
                "Step 6: Reset the Viewer\n"
                "Before importing a new image file, reset the viewer to avoid overlapping of image layers.\n"
                "You can use the reset viewer or simply use the 'Reset' button provided in the widget."
            )

            label.setFontPointSize(30)

            layout.addWidget(label)

            self.instruction_window.setLayout(layout)
            self.instruction_window.adjustSize()
            self.instruction_window.show()
    
    def close_instruction_window(self, event):
        self.instruction_window.close()