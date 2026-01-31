import cv2
import numpy as np

def segment_and_get_bounding_boxes(image):
    # Ensure image is grayscale
    if len(image.shape) > 2 and image.shape[2] > 1:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(image)
    
    # Apply noise reduction and edge preservation
    blurred = cv2.bilateralFilter(enhanced, 9, 75, 75)
    
    # Use more sophisticated thresholding
    binary_image = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY_INV, 13, 2)
    
    # Apply morphological operations to improve segmentation
    kernel = np.ones((3, 3), np.uint8)
    binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel, iterations=1)
    binary_image = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Find contours
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours by area and shape
    min_contour_area = 40
    max_contour_area = 1000
    filtered_contours = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_contour_area <= area <= max_contour_area:
            # Check circularity/elongation to identify bacteria-like shapes
            perimeter = cv2.arcLength(cnt, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if 0.3 <= circularity <= 0.9:  # Typical bacteria shape range
                    filtered_contours.append(cnt)
    
    # Get bounding boxes
    bounding_boxes = []
    for cnt in filtered_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Add a smaller padding around the box
        padding = 3
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2*padding)
        h = min(image.shape[0] - y, h + 2*padding)
        
        # Ensure minimum size for detection
        if w >= 10 and h >= 10:
            bounding_boxes.append((x, y, w, h))
    
    # Merge overlapping boxes instead of just filtering them
    merged_boxes = []
    if bounding_boxes:
        # Convert to x1, y1, x2, y2 format for easier merging
        boxes = np.array([[x, y, x+w, y+h] for x, y, w, h in bounding_boxes])
        
        # Find connected components of overlapping boxes
        remaining_boxes = list(range(len(boxes)))
        merged_indices = []
        
        while remaining_boxes:
            # Start a new merged group
            current_group = [remaining_boxes[0]]
            remaining_boxes.pop(0)
            
            # Grow the group by adding all overlapping boxes
            i = 0
            while i < len(current_group):
                idx = current_group[i]
                j = 0
                while j < len(remaining_boxes):
                    # Check overlap between box idx and box j
                    box1 = boxes[idx]
                    box2 = boxes[remaining_boxes[j]]
                    
                    # Calculate intersection
                    x_overlap = max(0, min(box1[2], box2[2]) - max(box1[0], box2[0]))
                    y_overlap = max(0, min(box1[3], box2[3]) - max(box1[1], box2[1]))
                    
                    if x_overlap > 0 and y_overlap > 0:
                        # Boxes overlap, add to current group
                        current_group.append(remaining_boxes[j])
                        remaining_boxes.pop(j)
                    else:
                        j += 1
                i += 1
            
            # Add the group to merged indices
            merged_indices.append(current_group)
        
        # For each connected component, create a single bounding box
        for group in merged_indices:
            group_boxes = boxes[group]
            # Get the minimum and maximum coordinates to create a single enclosing box
            x1 = np.min(group_boxes[:, 0])
            y1 = np.min(group_boxes[:, 1])
            x2 = np.max(group_boxes[:, 2])
            y2 = np.max(group_boxes[:, 3])
            
            # Convert back to x, y, w, h format
            merged_boxes.append((int(x1), int(y1), int(x2-x1), int(y2-y1)))
    
    # Prepare output image
    image_with_boxes = image.copy()
    if len(image_with_boxes.shape) == 2:  # If grayscale
        image_with_boxes = cv2.cvtColor(image_with_boxes, cv2.COLOR_GRAY2BGR)
    
    for box in merged_boxes:
        x, y, w, h = box
        cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (255, 0, 0), 1)

    return merged_boxes, image_with_boxes
