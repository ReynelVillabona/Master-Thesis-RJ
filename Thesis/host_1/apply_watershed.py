import numpy as np
import os
import json

OPENSLIDE_PATH = "/usr/local/lib/python3.8/site-packages/openslide"

if hasattr(os, 'add_dll_directory'):
    # Python >= 3.8 on Windows
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
else:
    import openslide
    
import openslide
import cv2

input_folder_path = "/app/paleo_images"

def apply_watershed(input_folder_path):
    
    
    output_folder_path = "/app/watershed_images"

    # Create the output folder if it does not exist
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)
        
    count_watershed_images = 0



    # Loop through all the images in the input folder
    for filename in os.listdir(input_folder_path):
        if filename.endswith('.jpg') and not filename.endswith('_seg.jpg'):  # assuming all images are JPEG files
            # Load the image and convert it to grayscale
            input_img_path = os.path.join(input_folder_path, filename)
            img = cv2.imread(input_img_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply thresholding to separate the foreground (microfossils) from the background
            ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
                # Apply morphological opening to remove small objects and noise
            kernel = np.ones((3,3), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

            # Apply distance transform to obtain the distance map
            dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)

                # Apply thresholding to the distance map to obtain the foreground markers
            ret, fg_markers = cv2.threshold(dist_transform, 0.5*dist_transform.max(), 255, 0)

                # Apply watershed algorithm to segment the foreground markers and obtain the labels
            fg_markers = np.uint8(fg_markers)
            unknown = cv2.subtract(opening, fg_markers)
            ret, bg_markers = cv2.threshold(unknown, 0, 255, cv2.THRESH_BINARY_INV)
            bg_markers = cv2.dilate(bg_markers, kernel, iterations=3)
            markers = cv2.add(fg_markers, bg_markers)

                # Convert the grayscale image to a 3-channel format
            img_color = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Apply the watershed segmentation algorithm
            markers = markers.astype(np.int32)
            markers_copy = markers.copy()
            cv2.watershed(img_color, markers_copy)

                # Visualize the segmented image and the markers
            img_color[markers_copy == -1] = [255,0,0]

                # Save the segmented image to the output folder
            output_img_path = os.path.join(output_folder_path, 'img_'+str(filename)+'_seg.jpg')
            cv2.imwrite(output_img_path, img_color)
            count_watershed_images += 1
    
    return json.dumps({"count_watershed_images": count_watershed_images })

output = apply_watershed(input_folder_path)
print(output)