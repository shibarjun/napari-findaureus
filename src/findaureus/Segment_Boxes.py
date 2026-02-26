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
    
    # Filter contours by area and shape (relaxed to capture small/clustered bacteria)
    min_contour_area = 16    # lowered to include smaller objects
    max_contour_area = 5000  # raised to allow larger clusters
    filtered_contours = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_contour_area or area > max_contour_area:
            continue
        # Check circularity/elongation to identify bacteria-like shapes
        perimeter = cv2.arcLength(cnt, True)
        if perimeter <= 0:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        # Relax circularity bounds to include elongated and clustered shapes
        if 0.08 <= circularity <= 1.2:
            filtered_contours.append(cnt)
    
    # Get bounding boxes
    bounding_boxes = []
    for cnt in filtered_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Add padding around the box (proportional to box size)
        padding = max(5, int(0.25 * max(w, h)))
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
        
        # Find connected components of overlapping or nearby boxes
        # Expand boxes slightly before grouping so nearby boxes (close clusters) merge
        merge_margin = 10
        expanded = boxes.copy()
        expanded[:, 0] = expanded[:, 0] - merge_margin
        expanded[:, 1] = expanded[:, 1] - merge_margin
        expanded[:, 2] = expanded[:, 2] + merge_margin
        expanded[:, 3] = expanded[:, 3] + merge_margin

        remaining_boxes = list(range(len(expanded)))
        merged_indices = []

        while remaining_boxes:
            current_group = [remaining_boxes[0]]
            remaining_boxes.pop(0)
            i = 0
            while i < len(current_group):
                idx = current_group[i]
                j = 0
                while j < len(remaining_boxes):
                    box1 = expanded[idx]
                    box2 = expanded[remaining_boxes[j]]
                    x_overlap = max(0, min(box1[2], box2[2]) - max(box1[0], box2[0]))
                    y_overlap = max(0, min(box1[3], box2[3]) - max(box1[1], box2[1]))
                    if x_overlap > 0 and y_overlap > 0:
                        current_group.append(remaining_boxes[j])
                        remaining_boxes.pop(j)
                    else:
                        j += 1
                i += 1
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

    # Create a filled mask of the filtered contours (bacteria-like shapes)
    mask = np.zeros_like(image, dtype=np.uint8)
    if filtered_contours:
        for cnt in filtered_contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Work within a lightly padded ROI so dilation stays near the bacteria footprint
            padding = max(2, int(0.05 * max(w, h)))
            x0 = max(0, x - padding)
            y0 = max(0, y - padding)
            x1 = min(image.shape[1], x + w + padding)
            y1 = min(image.shape[0], y + h + padding)

            roi_shape = (y1 - y0, x1 - x0)
            if roi_shape[0] <= 0 or roi_shape[1] <= 0:
                continue

            local_mask = np.zeros(roi_shape, dtype=np.uint8)

            # Shift contour into ROI coordinate space and draw its convex hull to cover full bacteria
            shifted_cnt = cnt.copy()
            shifted_cnt[:, 0, 0] -= x0
            shifted_cnt[:, 0, 1] -= y0
            hull = cv2.convexHull(shifted_cnt)
            cv2.drawContours(local_mask, [hull], -1, 255, thickness=cv2.FILLED)

            # Dilate/close inside the ROI to include faint edges without filling the entire box
            kernel_size = max(3, int(0.15 * max(w, h)))
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            local_mask = cv2.morphologyEx(local_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

            # Limit coverage to the segmented foreground (plus a small dilation) to avoid filling entire box
            segment_roi = binary_image[y0:y1, x0:x1]
            if segment_roi.size:
                limiter_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, kernel_size - 2), max(3, kernel_size - 2)))
                segment_limit = cv2.dilate(segment_roi, limiter_kernel, iterations=1)
                local_mask = cv2.bitwise_and(local_mask, segment_limit)

            # If mask is still almost as large as the ROI, erode slightly to keep it specific
            roi_area = (x1 - x0) * (y1 - y0)
            mask_pixels = int(cv2.countNonZero(local_mask))
            if roi_area > 0 and mask_pixels > 0.75 * roi_area:
                tighten_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                local_mask = cv2.erode(local_mask, tighten_kernel, iterations=1)

            # Merge ROI result back into the full-resolution mask
            mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], local_mask)

        # Light smoothing keeps edges clean without erasing coverage
        smooth_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, smooth_kernel, iterations=1)

    return merged_boxes, image_with_boxes, mask
