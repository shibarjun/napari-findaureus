from typing import TYPE_CHECKING
from .Module_Class import *
import napari.layers
import os
import pkg_resources

if TYPE_CHECKING:
    import napari

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit, QHBoxLayout, QTextEdit, QDialog, QSizePolicy
from qtpy.QtCore import Qt, QUrl
from qtpy.QtGui import QFont, QPixmap, QCursor, QDesktopServices

def open_url():
    QDesktopServices.openUrl(QUrl("https://github.com/shibarjun/napari-findaureus"))

class Find_Bacteria(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.analysis_active = False  # Add this flag
        self.init_ui()
        # Check for active layer on startup
        if len(self.viewer.layers) > 0:
            active_layer = self.viewer.layers.selection.active
            if active_layer is not None:
                self.update_image_info(active_layer)
        self.viewer.layers.selection.events.active.connect(self.on_layer_selection_change)
        self.viewer.layers.events.removed.connect(self.on_layers_removed)

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
        icon_fa_path = pkg_resources.resource_filename('findaureus', 'resources/application_icon.png')
        icon_fa = QPixmap(icon_fa_path)
        icon_fa = icon_fa.scaled(64, 64)
        fa_widget = QLabel()
        fa_widget.setPixmap(icon_fa)

        ##description
        description_widget = QPlainTextEdit()
        description_widget.setReadOnly(True)
        description_widget.setPlainText("Find bacteria in confocal laser scanning microscopy (CLSM) obtained infected bone tissue images.")
        description_widget.setFixedSize(256, 64)
        
        ##conclude the content
        content_layout_1.addWidget(fa_widget)
        content_layout_1.addWidget(description_widget)
        layout.addWidget(content_widget_1, alignment=Qt.AlignCenter)
        
        #github and instruction content
        content_widget_2 = QWidget()
        content_layout_2 = QHBoxLayout(content_widget_2)

        ##github icon
        icon_gh_path = pkg_resources.resource_filename('findaureus', 'resources/GitHub-Mark-Light-32px.png')
        icon_gh = QPixmap(icon_gh_path)
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
        
        # Add section for general image info with border
        info_container = QWidget()
        container_style = "QWidget { border: 1px solid gray; border-radius: 3px; padding: 5px; }"
        info_container.setStyleSheet(container_style)
        info_layout = QVBoxLayout()
        
        self.general_info_label = QLabel("Image Information")
        self.general_info_label.setFont(labelfont)
        self.general_info_label.setStyleSheet("font-weight: bold; border: none;")
        info_layout.addWidget(self.general_info_label)

        self.image_info = QLabel("")
        self.image_info.setFont(labelfont)
        self.image_info.setStyleSheet("border: none;")
        info_layout.addWidget(self.image_info)
        
        info_container.setLayout(info_layout)
        layout.addWidget(info_container)

        # Add section for analysis results with the same border style
        self.analysis_container = QWidget()
        self.analysis_container.setStyleSheet(container_style)
        self.analysis_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        analysis_layout = QVBoxLayout(self.analysis_container)
        analysis_layout.setSpacing(8)  # Increased spacing
        
        self.analysis_label = QLabel("Analysis Results")
        self.analysis_label.setFont(labelfont)
        self.analysis_label.setStyleSheet("font-weight: bold; border: none;")
        analysis_layout.addWidget(self.analysis_label)
        
        self.analysis_info = QLabel("No analysis performed yet")
        self.analysis_info.setFont(labelfont)
        self.analysis_info.setStyleSheet("border: none;")
        self.analysis_info.setWordWrap(True)
        self.analysis_info.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        analysis_layout.addWidget(self.analysis_info)
        
        layout.addWidget(self.analysis_container)

        self.setLayout(layout)
        self.instruction_window = None
        
    def for_napari(image_list):
        data =np.stack(image_list)
        data = np.expand_dims(data, -1)
        data = data.transpose(3,0,1,2)
        data = np.expand_dims(data, axis=0)
        return(data)

    def get_roi_from_layer(self, layer):
        """Extract ROI from selected shapes/labels in the viewer"""
        shapes = [x for x in self.viewer.layers if isinstance(x, napari.layers.Shapes)]
        if not shapes:
            return None, None, None
            
        shape_layer = shapes[0]
        if len(shape_layer.data) == 0:
            return None, None, None
            
        # Get the first shape's data
        bbox = shape_layer.data[0]
        if bbox.ndim > 1:
            mins = np.min(bbox, axis=0)
            maxs = np.max(bbox, axis=0)
            
            # Get ROI dimensions in pixels and microns
            height_px = int(np.ceil(maxs[-2]) - np.floor(mins[-2]))
            width_px = int(np.ceil(maxs[-1]) - np.floor(mins[-1]))
            
            slice_coords = []
            for min_val, max_val in zip(mins[-2:], maxs[-2:]):
                start = max(0, int(np.floor(min_val)))
                end = int(np.ceil(max_val))
                slice_coords.append(slice(start, end))
                
            roi_info = {
                'start_y': slice_coords[0].start,
                'start_x': slice_coords[1].start,
                'height_px': height_px,
                'width_px': width_px
            }
            
            bounds = np.array([mins[-2:], maxs[-2:]])
            return slice_coords, bounds, roi_info
                
        return None, None, None

    def FindBacteria(self) -> "napari.types.LayerDataTuple":
        self.analysis_active = True  # Set flag when analysis starts
        current_layer = self.viewer.layers.selection.active
        if current_layer is None:
            self.analysis_info.setText("No layer selected")
            self.analysis_active = False  # Reset flag if no layer is selected
            return

        # Check if the selected layer is a Shapes layer
        if isinstance(current_layer, napari.layers.Shapes):
            self.analysis_info.setText(
                "ROI Selection Active:\n"
                "After selecting the desired shape for your ROI, "
                "please select the image channel containing bacteria and then press 'Find bacteria!' again."
            )
            self.analysis_active = False # Reset flag as analysis is not proceeding
            return

        # Get ROI if selected
        roi_slices, bounds, roi_info = self.get_roi_from_layer(current_layer)
        image_list = list(current_layer.data[0,:,:,:])
        _,scalez,scalex,scaley = current_layer.scale
        scalexy = (scalex,scaley)
        scalezxy = (scalez,scaley,scalex)

        # Set analysis info to "Processing..." while running
        self.analysis_info.setText("Processing...")
        self.analysis_info.repaint()  # Force immediate update

        # Crop to ROI if present
        if roi_slices:
            cropped_list = []
            for img in image_list:
                cropped = img[roi_slices[0], roi_slices[1]]
                cropped_list.append(cropped)
            image_list = cropped_list
            # Update scale for cropped region
            scalezxy = (scalez, (bounds[0][1]-bounds[0][0])*scalex, 
                      (bounds[1][1]-bounds[1][0])*scaley)

        try:
            # Process image for bacteria detection
            bac_image_list, bac_image_list_mask, bac_centroid_xy_coordinates, no_bac_dict, bac_pixelwise_xy_coordinates, bacteria_area = ReadImage.FindBacteriaAndNoBacteria(image_list, scalexy)
            # Convert results for napari display
            bac_data_mask = Find_Bacteria.for_napari(bac_image_list_mask)
            bac_data_bb = Find_Bacteria.for_napari(bac_image_list)
            self.bac_dict = bac_centroid_xy_coordinates
            # Calculate total bacteria
            total_bacteria = sum(len(coords) for coords in bac_centroid_xy_coordinates.values())

            # If ROI is selected, show ROI info and bacterial regions in current z plane in analysis_info
            if roi_slices and roi_info:
                roi_area_um2 = roi_info['height_px'] * scalex * roi_info['width_px'] * scalex
                layer_name, layer_height_um, layer_height_px, layer_width_um, layer_width_px, depth_um, _ = Find_Bacteria.for_raw_layer(current_layer)
                analysis_text = [
                    "ROI Analysis:",
                    f"ROI height: {roi_info['height_px']*scalex:.2f} μm ({roi_info['height_px']} px)",
                    f"ROI width: {roi_info['width_px']*scalex:.2f} μm ({roi_info['width_px']} px)",
                    f"ROI area: {roi_area_um2:.2f} μm²",
                ]
                if depth_um > 0:
                    roi_volume_um3 = roi_area_um2 * depth_um
                    analysis_text.append(f"ROI volume: {roi_volume_um3:.2f} μm³")
                # Only show bacterial regions in current plane
                try:
                    current_z_plane = int(self.viewer.dims.current_step[2])
                except Exception:
                    current_z_plane = 0
                key = f"xy_Z_{current_z_plane}"
                bac_found = len(bac_centroid_xy_coordinates.get(key, []))
                analysis_text.append(f"Bacterial regions in current plane: {bac_found}")
                self.analysis_info.setText("\n".join(analysis_text))
                self.analysis_info.repaint()
                self._last_roi_info = {
                    'roi_info': roi_info,
                    'scalex': scalex,
                    'depth_um': depth_um
                }
            else:
                self._last_roi_info = None
                analysis_text = []
                analysis_text.extend([
                    f"Z planes with bacteria: {len(bac_centroid_xy_coordinates)}",
                    f"Z planes without bacteria: {len(no_bac_dict)}",
                    f"Total bacteria detected: {total_bacteria}"
                ])
                # Only show bacterial regions in current plane
                try:
                    current_z_plane = int(self.viewer.dims.current_step[2])
                except Exception:
                    current_z_plane = 0
                key = f"xy_Z_{current_z_plane}"
                bac_found = len(bac_centroid_xy_coordinates.get(key, []))
                analysis_text.append(f"Bacterial regions in current plane: {bac_found}")
                self.analysis_info.setText("\n".join(analysis_text))
                self.analysis_info.repaint()

            # Connect Z-plane change event for 3D images
            if scalez != 1:
                self.viewer.dims.events.current_step.connect(self.on_active_layer_change)

            # Add processed layers with transparency
            suffix = "_ROI" if roi_slices else ""
            # Create bounding box layer with only the boxes visible
            self.viewer.add_image(
                bac_data_bb, 
                name=f"{current_layer.name}_Bounding box{suffix}", 
                scale=scalezxy,
                opacity=1.0,
                contrast_limits=[254, 255],  # Only show the bright box lines
                gamma=1.0,
                rendering='translucent',
                blending='additive',
                visible=True,
                colormap='yellow'  # Make boxes more visible
            )
            # Add mask with high contrast red highlights
            self.viewer.add_image(
                bac_data_mask,
                name=f"{current_layer.name}_Bacteria mask{suffix}", 
                scale=scalezxy,
                opacity=1.0,
                colormap='red',
                contrast_limits=[128, 255],
                rendering='translucent',
                blending='additive',
                visible=True
            )

            # Force update of analysis box for current z-plane
            self.on_active_layer_change()

        except Exception as e:
            self.analysis_info.setText(f"Error during analysis: {str(e)}")
            self.analysis_info.repaint()
            self.analysis_active = False  # Reset flag on error
            return

    def reset_viewer_and_widget(self):
        self.viewer.layers.select_all()
        self.viewer.layers.remove_selected()
        self.analysis_active = False  # Reset flag when resetting widget
        self.clear_texts_and_labels()

    def for_raw_layer(active_layer):
        
        _,scalez,scalex ,scaley  = active_layer.scale
        layer_name = active_layer.name
        layer_shape = active_layer.data.shape
        z_layer, layer_height_px, layer_width_px = layer_shape[1],layer_shape[2],layer_shape[3]
        depth_um, layer_height_um, layer_width_um = z_layer*scalez, layer_height_px*scalex, layer_width_px*scaley
        return(layer_name, layer_height_um, layer_height_px, layer_width_um, layer_width_px, depth_um,scalex)
    
    def update_image_info(self, layer, roi_info=None):
        try:
            layer_name, layer_height_um, layer_height_px, layer_width_um, layer_width_px, depth_um, scalex = Find_Bacteria.for_raw_layer(layer)
            # If ROI info is provided, use ROI dimensions for area/volume
            if roi_info:
                roi_area_um2 = roi_info['height_px'] * scalex * roi_info['width_px'] * scalex
                info_text = (
                    f"Channel selected: {layer_name}\n"
                    f"ROI height: {roi_info['height_px']*scalex:.2f} μm ({roi_info['height_px']} px)\n"
                    f"ROI width: {roi_info['width_px']*scalex:.2f} μm ({roi_info['width_px']} px)\n"
                    f"ROI area: {roi_area_um2:.2f} μm²\n"
                )
                # If depth > 0, show ROI volume
                if depth_um > 0:
                    roi_volume_um3 = roi_area_um2 * depth_um
                    info_text += f"ROI volume: {roi_volume_um3:.2f} μm³\n"
            else:
                area_um2 = layer_height_um * layer_width_um
                info_text = (
                    f"Channel selected: {layer_name}\n"
                    f"Image height: {layer_height_um:.2f} μm ({layer_height_px} px)\n"
                    f"Image width: {layer_width_um:.2f} μm ({layer_width_px} px)\n"
                    f"Image depth: {depth_um:.2f} μm\n"
                    f"Image area: {area_um2:.2f} μm²\n"
                    f"Image resolution: {round(1/scalex)} pixels per μm"
                )
                if depth_um > 0:
                    volume_um3 = area_um2 * depth_um
                    info_text += f"\nImage volume: {volume_um3:.2f} μm³"
            self.image_info.setText(info_text)
        except Exception:
            pass

    def on_layer_selection_change(self, event):
        active_layer = event.value
        self.update_image_info(active_layer)
        if not self.analysis_active:  # Only reset if no analysis is active
            self.analysis_info.setText("No analysis performed yet")
            
    def on_active_layer_change(self):
        # For ROI, keep ROI info and update only the bacterial region count, keeping area/volume info consistent
        if hasattr(self, '_last_roi_info') and self._last_roi_info:
            roi_info = self._last_roi_info['roi_info']
            scalex = self._last_roi_info['scalex']
            depth_um = self._last_roi_info['depth_um']
            try:
                current_z_plane = int(self.viewer.dims.current_step[2])
            except Exception:
                current_z_plane = 0
            bacteria_dic = self.bac_dict
            key = f"xy_Z_{current_z_plane}"
            bac_found = len(bacteria_dic.get(key, []))
            roi_area_um2 = roi_info['height_px'] * scalex * roi_info['width_px'] * scalex
            analysis_text = [
                "ROI Analysis:",
                f"ROI height: {roi_info['height_px']*scalex:.2f} μm ({roi_info['height_px']} px)",
                f"ROI width: {roi_info['width_px']*scalex:.2f} μm ({roi_info['width_px']} px)",
                f"ROI area: {roi_area_um2:.2f} μm²",
            ]
            if depth_um > 0:
                roi_volume_um3 = roi_area_um2 * depth_um
                analysis_text.append(f"ROI volume: {roi_volume_um3:.2f} μm³")
            analysis_text.append(f"Bacterial regions in current plane: {bac_found}")
            self.analysis_info.setText("\n".join(analysis_text))
            self.analysis_info.repaint()
        else:
            try:
                current_z_plane = int(self.viewer.dims.current_step[2])
            except Exception:
                current_z_plane = 0
            bacteria_dic = self.bac_dict
            key = f"xy_Z_{current_z_plane}"
            bac_found = len(bacteria_dic.get(key, []))
            curr_analysis = self.analysis_info.text().split("\n")
            if curr_analysis and curr_analysis[-1].startswith("Bacterial regions in current plane"):
                curr_analysis = curr_analysis[:-1]
            curr_analysis.append(f"Bacterial regions in current plane: {bac_found}")
            self.analysis_info.setText("\n".join(curr_analysis))
            self.analysis_info.repaint()

    def clear_texts_and_labels(self):
        self.image_info.setText("")
        self.analysis_info.setText("")
        
    def open_instruction(self):
        if not self.instruction_window or not self.instruction_window.isVisible():
            self.instruction_window = QDialog()
            self.instruction_window = QDialog(parent=self)
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
                "Use the 'Reset' button provided in the widget."
                )

            label.setFontPointSize(30)

            layout.addWidget(label)

            self.instruction_window.setLayout(layout)
            self.instruction_window.adjustSize()
            self.instruction_window.show()
    
    def closeEvent(self, event):
        self.instruction_window.close()
        if self.instruction_window:
            self.instruction_window.close()
        super().closeEvent(event)

    def on_layers_removed(self, event):
        # Clear analysis info if both bounding box and mask layers are deleted
        layer_names = [layer.name for layer in self.viewer.layers]
        has_bbox = any(name.endswith("_Bounding box") or "_Bounding box" in name for name in layer_names)
        has_mask = any(name.endswith("_Bacteria mask") or "_Bacteria mask" in name for name in layer_names)
        if not has_bbox and not has_mask:
            self.analysis_info.setText("")
