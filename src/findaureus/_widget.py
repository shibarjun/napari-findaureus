from typing import TYPE_CHECKING
from .Module_Class import *
import napari.layers
import os
from importlib.resources import files

if TYPE_CHECKING:
    import napari

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QPlainTextEdit, QHBoxLayout, QTextEdit, QDialog, QSizePolicy, QFileDialog, QMessageBox
from qtpy.QtCore import Qt, QUrl
from qtpy.QtGui import QFont, QPixmap, QCursor, QDesktopServices

def open_url():
    QDesktopServices.openUrl(QUrl("https://github.com/shibarjun/napari-findaureus"))

class Find_Bacteria(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        self.analysis_active = False  # Add this flag
        self._latest_analysis_data = None
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
        icon_fa_path = str(files('findaureus').joinpath('resources/application_icon.png'))
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
        icon_gh_path = str(files('findaureus').joinpath('resources/GitHub-Mark-Light-32px.png'))
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

        self.image_info = QPlainTextEdit()
        self.image_info.setReadOnly(True)
        self.image_info.setFont(labelfont)
        self.image_info.setStyleSheet("border: none;")
        self.image_info.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.image_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
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
        
        self.analysis_info = QPlainTextEdit()
        self.analysis_info.setReadOnly(True)
        self.analysis_info.setFont(labelfont)
        self.analysis_info.setStyleSheet("border: none;")
        self.analysis_info.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.analysis_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.analysis_info.setPlainText("No analysis performed yet")
        analysis_layout.addWidget(self.analysis_info)
        
        layout.addWidget(self.analysis_container)

        self.export_button = QPushButton("Export results")
        self.export_button.setFont(buttonfont)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_results)
        layout.addWidget(self.export_button, alignment=Qt.AlignRight)

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
        self.export_button.setEnabled(False)
        self._latest_analysis_data = None
        current_layer = self.viewer.layers.selection.active
        if current_layer is None:
            self.analysis_info.setPlainText("No layer selected")
            self.analysis_active = False  # Reset flag if no layer is selected
            self.export_button.setEnabled(False)
            self._latest_analysis_data = None
            return

        # Check if the selected layer is a Shapes layer
        if isinstance(current_layer, napari.layers.Shapes):
            self.analysis_info.setPlainText(
                "ROI Selection Active:\n"
                "After selecting the desired shape for your ROI, "
                "please select the image channel containing bacteria and then press 'Find bacteria!' again."
            )
            self.analysis_active = False # Reset flag as analysis is not proceeding
            self.export_button.setEnabled(False)
            self._latest_analysis_data = None
            return

        # Get ROI if selected
        roi_slices, bounds, roi_info = self.get_roi_from_layer(current_layer)
        image_list = list(current_layer.data[0,:,:,:])
        _,scalez,scalex,scaley = current_layer.scale
        scalexy = (scalex,scaley) # This is (sY, sX for processing)
        # scalezxy = (scalez,scaley,scalex) # Original user's ZXY scale order, potentially problematic

        # Correct scale for (T,C,Z,Y,X) data based on dimensional meaning
        # scalez = Z-dim scale, scalex = Y-dim scale, scaley = X-dim scale
        napari_layer_scale = (1, 1, scalez, scalex, scaley)
        napari_layer_translate = (0, 0, 0, 0, 0) # Default T,C,Z,Y,X translation

        # Set analysis info to "Processing..." while running
        self.analysis_info.setPlainText("Processing...")
        self.analysis_info.repaint()  # Force immediate update

        # Crop to ROI if present
        if roi_slices:
            cropped_list = []
            for img in image_list:
                cropped = img[roi_slices[0], roi_slices[1]]
                cropped_list.append(cropped)
            image_list = cropped_list
            # Update scale for cropped region - THIS IS REMOVED as it's incorrect
            # scalezxy = (scalez, (bounds[0][1]-bounds[0][0])*scalex, 
            #           (bounds[1][1]-bounds[1][0])*scaley)

            # Calculate translation for the ROI based on its start coordinates and original scales
            # roi_info['start_y'] is pixel offset in Y, roi_info['start_x'] is pixel offset in X.
            # scalex is sY (scale of Y dim), scaley is sX (scale of X dim).
            translate_z_world = 0 
            translate_y_world = roi_info['start_y'] * scalex # Y-offset_px * Y-scale
            translate_x_world = roi_info['start_x'] * scaley # X-offset_px * X-scale
            napari_layer_translate = (0, 0, translate_z_world, translate_y_world, translate_x_world)
            # The napari_layer_scale remains the same as the original image's pixel scale.

        try:
            # Process image for bacteria detection
            bac_image_list, bac_image_list_mask, bac_centroid_xy_coordinates, no_bac_dict, bac_pixelwise_xy_coordinates, _ = ReadImage.FindBacteriaAndNoBacteria(image_list, scalexy) # Original bacteria_area is per-contour

            # Calculate bacteria area per Z-plane from the mask
            self.bacteria_area_per_z_plane = {}
            total_bacteria_area_from_mask = 0
            # scalex from layer.scale is sY (Y-axis scale), scaley is sX (X-axis scale)
            pixel_area_um2 = scalex * scaley 
            self.pixel_area_um2 = pixel_area_um2 # Store for on_active_layer_change

            if bac_image_list_mask: # Ensure it's not None or empty
                for z_idx, z_mask_plane in enumerate(bac_image_list_mask):
                    if isinstance(z_mask_plane, np.ndarray):
                        num_bacteria_pixels = np.count_nonzero(z_mask_plane)
                        area_um2 = num_bacteria_pixels * pixel_area_um2
                        self.bacteria_area_per_z_plane[z_idx] = area_um2
                        total_bacteria_area_from_mask += area_um2
                    else:
                        self.bacteria_area_per_z_plane[z_idx] = 0
            
            # Results will be converted for napari display below when present
            self.bac_dict = bac_centroid_xy_coordinates
            # Calculate total bacteria count
            total_bacteria_count = sum(len(coords) for coords in bac_centroid_xy_coordinates.values())

            # Determine current Z plane for initial display
            try:
                current_z_plane_idx = int(self.viewer.dims.current_step[2])
            except Exception:
                current_z_plane_idx = 0

            area_in_current_plane_um2 = self.bacteria_area_per_z_plane.get(current_z_plane_idx, 0)
            bac_count_in_current_plane = len(self.bac_dict.get(f"xy_Z_{current_z_plane_idx}", []))
            bacteria_info_current_plane_str = f"Bacteria in current Z plane: {bac_count_in_current_plane} ({area_in_current_plane_um2:.2f} µm²)"

            # If ROI is selected, show ROI info and bacterial regions in current z plane in analysis_info
            if roi_slices and roi_info:                
                roi_physical_height = roi_info['height_px'] * scalex # Y-pixels * Y-scale
                roi_physical_width = roi_info['width_px'] * scaley  # X-pixels * X-scale
                roi_area_um2 = roi_physical_height * roi_physical_width # 2D area of the ROI shape

                _, _, _, _, _, depth_um, _ = Find_Bacteria.for_raw_layer(current_layer) # depth_um is for original layer
                
                analysis_text = [
                    "ROI Analysis:",
                    f"ROI height: {roi_physical_height:.2f} µm ({roi_info['height_px']} px)",
                    f"ROI width: {roi_physical_width:.2f} µm ({roi_info['width_px']} px)",
                    f"ROI area (2D shape): {roi_area_um2:.2f} µm²",
                    f"Total bacteria area in ROI (sum over Z): {total_bacteria_area_from_mask:.2f} µm²",
                ]
                
                num_z_planes_in_roi_local = len(image_list) # Define it here for local use in _last_roi_info

                # Percentage calculation lines are removed from analysis_text population

                analysis_text.append(bacteria_info_current_plane_str) # Z-specific info
                self.analysis_info.setPlainText("\n".join(analysis_text))
                self.analysis_info.repaint()
                self._last_roi_info = {
                    'roi_info': roi_info,
                    'scalex': scalex, # sY
                    'scaley': scaley, # sX
                    'depth_um': depth_um, # Original layer depth
                    'roi_area_um2': roi_area_um2,
                    'total_bacteria_area_in_roi': total_bacteria_area_from_mask,
                    'num_z_planes_in_roi': num_z_planes_in_roi_local, # Use the locally defined variable
                    # Keep calculation for internal use, just not displayed
                    'percentage_bacteria_in_roi': (total_bacteria_area_from_mask / (roi_area_um2 * num_z_planes_in_roi_local)) * 100 if roi_area_um2 > 0 and num_z_planes_in_roi_local > 0 else 0
                }
            else: # No ROI (full image analysis)
                self._last_roi_info = None
                analysis_text = [
                    f"Z planes with bacteria: {len(bac_centroid_xy_coordinates)}",
                    f"Z planes without bacteria: {len(no_bac_dict)}",
                    f"Total bacteria count: {total_bacteria_count}",
                    f"Total bacteria area (sum over Z): {total_bacteria_area_from_mask:.2f} µm²"
                ]
                analysis_text.append(bacteria_info_current_plane_str) # Z-specific info
                self.analysis_info.setPlainText("\n".join(analysis_text))
                self.analysis_info.repaint()

            # store analysis export data
            self._latest_analysis_data = {
                'file_name': self.get_layer_filename(current_layer),
                'channel_name': current_layer.name,
                'image_height_px': current_layer.data.shape[2],
                'image_width_px': current_layer.data.shape[3],
                'scale_z': scalez,
                'scale_y': scalex,
                'scale_x': scaley,
                'roi': bool(roi_slices and roi_info),
                'roi_info': roi_info,
                'total_bacteria_count': total_bacteria_count,
                'total_bacteria_area_um2': total_bacteria_area_from_mask,
                'z_plane_count': len(image_list),
                'bacteria_area_per_z_plane': self.bacteria_area_per_z_plane,
                'bac_centroid_xy_coordinates': bac_centroid_xy_coordinates,
                'no_bac_dict': no_bac_dict,
                'roi_tracking': {
                    'num_z_planes': num_z_planes_in_roi_local if roi_slices and roi_info else len(image_list)
                }
            }
            self.export_button.setEnabled(True)

            # Connect Z-plane change event for 3D images
            try:
                self.viewer.dims.events.current_step.disconnect(self.on_active_layer_change)
            except (TypeError, RuntimeError): # TypeError if never connected, RuntimeError if napari already cleaned it up
                pass # Not connected or already disconnected

            if scalez != 1:
                self.viewer.dims.events.current_step.connect(self.on_active_layer_change)

            # Add processed layers with transparency
            suffix = "_ROI" if roi_slices else ""
            bbox_name = f"{current_layer.name}_Bounding box{suffix}"
            mask_name = f"{current_layer.name}_Bacteria mask{suffix}"

            # Add bounding box layer only if bacteria centroids were detected
            if total_bacteria_count > 0 and bac_image_list and len(bac_image_list) > 0:
                bbox_layer = Find_Bacteria.for_napari(bac_image_list)
                self._bbox_layer_name = bbox_name
                self.viewer.add_image(
                    bbox_layer,
                    name=bbox_name,
                    scale=napari_layer_scale,
                    translate=napari_layer_translate,
                    opacity=1.0,
                    gamma=1.0,
                    rendering='translucent',
                    blending='additive',
                    visible=True,
                    colormap='yellow'
                )

            # Add mask layer only if we have masks
            if bac_image_list_mask and len(bac_image_list_mask) > 0:
                mask_layer = Find_Bacteria.for_napari(bac_image_list_mask)
                self._mask_layer_name = mask_name
                self.viewer.add_image(
                    mask_layer,
                    name=mask_name,
                    scale=napari_layer_scale,
                    translate=napari_layer_translate,
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
            self.analysis_info.setPlainText(f"Error during analysis: {str(e)}")
            self.analysis_info.repaint()
            self.analysis_active = False  # Reset flag on error
            self.export_button.setEnabled(False)
            self._latest_analysis_data = None
            return

    def reset_viewer_and_widget(self):
        # Temporarily disable Qt canvas updates to avoid race conditions
        # where VisPy/napari tries to redraw while layers are being removed.
        canvas_native = None
        try:
            canvas = getattr(self.viewer.window, 'qt_viewer', None)
            if canvas is not None:
                canvas_native = getattr(canvas, 'canvas', None)
                if canvas_native is not None:
                    # `native` is the underlying Qt widget
                    try:
                        canvas_native.native.setUpdatesEnabled(False)
                    except Exception:
                        pass

            # Remove layers (selection -> remove) while updates are paused
            self.viewer.layers.select_all()
            self.viewer.layers.remove_selected()

        finally:
            # Re-enable canvas updates and request a repaint
            try:
                if canvas_native is not None:
                    try:
                        canvas_native.native.setUpdatesEnabled(True)
                        canvas_native.native.update()
                    except Exception:
                        pass
            except Exception:
                pass

        try:
            self.viewer.dims.events.current_step.disconnect(self.on_active_layer_change)
        except (TypeError, RuntimeError):
            pass

        self.analysis_active = False  # Reset flag when resetting widget
        self.export_button.setEnabled(False)
        self._latest_analysis_data = None
        self.clear_texts_and_labels()

    def for_raw_layer(active_layer):
        
        _,scalez,scalex ,scaley  = active_layer.scale
        layer_name = active_layer.name
        layer_shape = active_layer.data.shape
        z_layer, layer_height_px, layer_width_px = layer_shape[1],layer_shape[2],layer_shape[3]
        depth_um, layer_height_um, layer_width_um = z_layer*scalez, layer_height_px*scalex, layer_width_px*scaley
        return(layer_name, layer_height_um, layer_height_px, layer_width_um, layer_width_px, depth_um,scalex)
    
    def get_layer_filename(self, layer):
        """Try several places to extract a filename for display in the widget."""
        try:
            # Check common metadata keys
            if hasattr(layer, 'metadata') and isinstance(layer.metadata, dict):
                for key in ('path', 'source', 'filename', 'file_name', 'image.path', 'uri', 'URI'):
                    if key in layer.metadata:
                        val = layer.metadata[key]
                        if isinstance(val, (list, tuple)) and val:
                            val = val[0]
                        if isinstance(val, str) and val:
                            return os.path.basename(val)

            # Check layer.source
            src = getattr(layer, 'source', None)
            if isinstance(src, (list, tuple)) and src:
                src = src[0]
            if isinstance(src, str) and src:
                return os.path.basename(src)

            # Fall back to layer.name if it looks like a filename
            name = getattr(layer, 'name', '')
            if isinstance(name, str) and '.' in name and len(name.split('.')[-1]) <= 6:
                return name
        except Exception:
            pass
        return 'Unknown'
    
    def update_image_info(self, layer, roi_info=None):
        try:
            layer_name, layer_height_um, layer_height_px, layer_width_um, layer_width_px, depth_um, scalex = Find_Bacteria.for_raw_layer(layer)
            filename = self.get_layer_filename(layer)
            # If ROI info is provided, use ROI dimensions for area/volume
            if roi_info:
                roi_area_um2 = roi_info['height_px'] * scalex * roi_info['width_px'] * scalex
                info_text = (
                    f"File: {filename}\n"
                    f"Channel selected: {layer_name}\n"
                    f"ROI height: {roi_info['height_px']*scalex:.2f} μm ({roi_info['height_px']} px)\n"
                    f"ROI width: {roi_info['width_px']*scalex:.2f} μm ({roi_info['width_px']} px)\n"
                    f"ROI area: {roi_area_um2:.2f} μm²\n"
                )                # If depth > 0, show ROI volume only if more than one z plane exists
                z_layer_count = layer.data.shape[1] if hasattr(layer, 'data') and isinstance(layer.data, np.ndarray) and layer.data.ndim > 3 else 0
                if depth_um > 0 and z_layer_count > 1:
                    roi_volume_um3 = roi_area_um2 * depth_um
                    info_text += f"ROI volume: {roi_volume_um3:.2f} μm³\n"
            else:
                area_um2 = layer_height_um * layer_width_um
                info_text = (
                    f"File: {filename}\n"
                    f"Channel selected: {layer_name}\n"
                    f"Image height: {layer_height_um:.2f} μm ({layer_height_px} px)\n"
                    f"Image width: {layer_width_um:.2f} μm ({layer_width_px} px)\n"
                    f"Image depth: {depth_um:.2f} μm\n"
                    f"Image area: {area_um2:.2f} μm²\n"
                    f"Image resolution: {round(1/scalex)} pixels per μm"                )
                # Only show volume if more than one z plane exists
                z_layer_count = layer.data.shape[1] if hasattr(layer, 'data') and isinstance(layer.data, np.ndarray) and layer.data.ndim > 3 else 0
                if depth_um > 0 and z_layer_count > 1:
                    volume_um3 = area_um2 * depth_um
                    info_text += f"\nImage volume: {volume_um3:.2f} μm³"
                self.image_info.setPlainText(info_text)
        except Exception:
            pass

    def on_layer_selection_change(self, event):
        active_layer = event.value
        self.update_image_info(active_layer)
        if not self.analysis_active:  # Only reset if no analysis is active
            self.analysis_info.setPlainText("No analysis performed yet")
            
    def on_active_layer_change(self):
        if not self.analysis_active or not hasattr(self, 'bac_dict') or \
           not hasattr(self, 'bacteria_area_per_z_plane') or not hasattr(self, 'pixel_area_um2'):
            return # Analysis not run or necessary data not available

        try:
            current_z_plane_idx = int(self.viewer.dims.current_step[2])
        except Exception:
            current_z_plane_idx = 0

        area_in_current_plane_um2 = self.bacteria_area_per_z_plane.get(current_z_plane_idx, 0)
        bac_count_in_current_plane = len(self.bac_dict.get(f"xy_Z_{current_z_plane_idx}", []))
        bacteria_info_current_plane_str = f"Bacteria in current Z plane: {bac_count_in_current_plane} ({area_in_current_plane_um2:.2f} µm²)"

        current_text = self.analysis_info.toPlainText()

        if "No analysis performed yet" == current_text.strip():
            # If the text is *only* the placeholder, do nothing.
            # FindBacteria is responsible for setting the initial analysis text.
            return

        # Filter out any existing "Bacteria in current Z plane:" lines
        # and any completely empty or whitespace-only lines from the previous text.
        lines_without_z_info = [
            line for line in current_text.split('\n') # This was one of the issues identified
            if line.strip() and not line.startswith("Bacteria in current Z plane:")
        ]

        # Append the new, updated Z-plane information line
        lines_without_z_info.append(bacteria_info_current_plane_str)
        
        self.analysis_info.setPlainText("\n".join(lines_without_z_info))
        self.analysis_info.repaint()

    def clear_texts_and_labels(self):
        self.image_info.setPlainText("")
        self.analysis_info.setPlainText("")
        
    def export_results(self):
        if not self._latest_analysis_data:
            QMessageBox.warning(self, "Export results", "No analysis results available to export.")
            return

        data = self._latest_analysis_data
        default_name = data.get('file_name', 'analysis_results')
        default_name = os.path.splitext(default_name)[0] + '_analysis'
        save_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save analysis results",
            default_name,
            "Text Files (*.txt);;CSV Files (*.csv)"
        )
        if not save_path:
            return

        ext = os.path.splitext(save_path)[1].lower()
        if not ext:
            ext = '.txt' if 'Text' in selected_filter else '.csv'
            save_path += ext

        try:
            if ext == '.csv':
                self._save_results_csv(save_path, data)
            else:
                self._save_results_txt(save_path, data)
            QMessageBox.information(self, "Export results", f"Export saved to {save_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export results", f"Unable to save file: {exc}")

    def _build_export_lines(self, data):
        lines = []
        lines.append("Image Information:")
        lines.append(f"File: {data.get('file_name', 'Unknown')}")
        lines.append(f"Channel selected: {data.get('channel_name', 'Unknown')}")
        image_height_um = data.get('image_height_px', 0) * data.get('scale_y', 1)
        image_width_um = data.get('image_width_px', 0) * data.get('scale_x', 1)
        depth_um = data.get('z_plane_count', 0) * data.get('scale_z', 1)
        if data.get('roi') and data.get('roi_info'):
            roi_info = data['roi_info']
            lines.append(f"ROI height: {roi_info['height_px'] * data.get('scale_y', 1):.2f} μm ({roi_info['height_px']} px)")
            lines.append(f"ROI width: {roi_info['width_px'] * data.get('scale_x', 1):.2f} μm ({roi_info['width_px']} px)")
            lines.append(f"ROI area: {roi_info['height_px'] * roi_info['width_px'] * data.get('scale_y', 1) * data.get('scale_x', 1):.2f} μm²")
            lines.append(f"ROI depth (Z planes): {data.get('z_plane_count', 0)}")
        else:
            lines.append(f"Image height: {image_height_um:.2f} μm ({data.get('image_height_px', 0)} px)")
            lines.append(f"Image width: {image_width_um:.2f} μm ({data.get('image_width_px', 0)} px)")
            lines.append(f"Image depth: {depth_um:.2f} μm")
            lines.append(f"Image area: {image_height_um * image_width_um:.2f} μm²")
            if data.get('scale_y', 0) > 0:
                lines.append(f"Image resolution: {round(1 / data.get('scale_y', 1))} pixels per μm")
        lines.append("")
        lines.append("Bacteria Analysis:")
        lines.append(f"Total bacteria count: {data.get('total_bacteria_count', 0)}")
        lines.append(f"Total bacteria area: {data.get('total_bacteria_area_um2', 0.0):.2f} µm²")
        lines.append("")
        lines.append("Z-plane bacteria count and area:")
        lines.append("Z plane\tBacteria count\tBacteria area (µm²)")
        z_plane_count = data.get('z_plane_count', 0)
        for z in range(z_plane_count):
            count = len(data.get('bac_centroid_xy_coordinates', {}).get(f"xy_Z_{z}", []))
            area = data.get('bacteria_area_per_z_plane', {}).get(z, 0.0)
            lines.append(f"{z}\t{count}\t{area:.2f}")
        return lines

    def _save_results_txt(self, path, data):
        lines = self._build_export_lines(data)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines))

    def _save_results_csv(self, path, data):
        lines = self._build_export_lines(data)
        with open(path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Image Information"])
            # write header lines as single-column rows until blank line
            for line in lines:
                if not line:
                    writer.writerow([])
                elif '\t' in line:
                    writer.writerow(line.split('\t'))
                else:
                    writer.writerow([line])

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
                "Welcome to the napari-findaureus Widget\n\n"
                "Step 1: Load Your Fluorescence Image File\n"
                "  - Supported formats: Zeiss (.czi), Leica (.lif), and Nikon (.nd2).\n"
                "  - Use the 'Open with Plugin' option in Napari (File > Open with Plugin > napari-findaureus) to load your image.\n\n"
                "Step 2: Explore Image & Select Channel\n"
                "  - Use the Napari viewer to explore your loaded image.\n"
                "  - Image information (dimensions, scale) will appear in the widget.\n"
                "  - Select the image layer/channel that contains the bacteria you want to analyze.\n\n"
                "Step 3: (Optional) Define a Region of Interest (ROI)\n"
                "  - If you want to analyze a specific area, use Napari's 'Shapes' layer tool (e.g., rectangle) to draw an ROI on your image.\n"
                "  - Ensure the Shapes layer is selected *before* selecting the image channel for analysis if you use an ROI.\n\n"
                "Step 4: Locate Bacteria\n"
                "  - Press the 'Find Bacteria!' button in the widget.\n"
                "  - If an ROI (Shapes layer) was active before selecting the image channel, analysis will be confined to that ROI.\n"
                "  - Two new layers will be added to the viewer:\n"
                "    - 'Bacteria mask': Highlights identified bacteria.\n"
                "    - 'Bounding boxes': Places boxes around detected bacteria.\n"
                "  - Analysis results (counts, area) will be displayed in the widget.\n\n"
                "Step 5: Explore Results\n"
                "  - Use Napari's features to view and analyze the results.\n"
                "  - If your image is 3D (has Z-planes), the analysis results in the widget will update as you scroll through Z-planes.\n\n"
                "Step 6: Reset for New Image\n"
                "  - Before loading a new image, press the 'Reset' button in the widget.\n"
                "  - This clears existing layers and analysis data to prevent overlap."
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
        # Prefer explicit stored names if available
        if hasattr(self, '_bbox_layer_name'):
            has_bbox = any(name == self._bbox_layer_name or self._bbox_layer_name in name for name in layer_names)
        else:
            has_bbox = any(name.endswith("_Bounding box") or "_Bounding box" in name for name in layer_names)

        if hasattr(self, '_mask_layer_name'):
            has_mask = any(name == self._mask_layer_name or self._mask_layer_name in name for name in layer_names)
        else:
            has_mask = any(name.endswith("_Bacteria mask") or "_Bacteria mask" in name for name in layer_names)

        if not has_bbox and not has_mask:
            self.analysis_info.setPlainText("")
            self.analysis_active = False
            self.export_button.setEnabled(False)
            self._latest_analysis_data = None
            # remove stored names so future analyses can reuse base names
            if hasattr(self, '_bbox_layer_name'):
                try:
                    del self._bbox_layer_name
                except Exception:
                    pass
            if hasattr(self, '_mask_layer_name'):
                try:
                    del self._mask_layer_name
                except Exception:
                    pass
