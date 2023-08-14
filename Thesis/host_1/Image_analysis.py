import numpy as np
import os
OPENSLIDE_PATH = "/usr/local/lib/python3.8/site-packages/openslide"

if hasattr(os, 'add_dll_directory'):
    # Python >= 3.8 on Windows
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
else:
    import openslide
    
import openslide
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
import cv2
import glob
import shutil

# Obtener la ruta del archivo .mrxs en el directorio /root
mrxs_file_path = glob.glob("/app/*.mrxs")[0]

# Abrir el slide utilizando el archivo .mrxs encontrado
slide = openslide.OpenSlide(mrxs_file_path)




 

def process_images(slide):
    
    


    tiles = DeepZoomGenerator(slide, tile_size=256, overlap=0, limit_bounds=False)
    
    folder_path = "/app/paleo_images"
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    Idx_max = 16
    

    for col in range(0, tiles.level_tiles[Idx_max][0]):
        for row in range(0, tiles.level_tiles[Idx_max][1]):
            tile = tiles.get_tile(Idx_max, (col, row))
            tile_array = np.array(tile)
            gray = cv2.cvtColor(tile_array, cv2.COLOR_RGB2GRAY)
            unique_values = np.unique(gray)
            if len(unique_values) >= 2 and unique_values[0] != 255 and unique_values[1] != 255:
                # Check if the mean pixel intensity is above a certain threshold
                if gray.mean() > 100:
                    # Check if the percentage of white pixels is below a certain threshold
                    white_percentage = np.count_nonzero(gray == 255) / gray.size
                    if white_percentage < 0.9:
                        tile_path = os.path.join(folder_path, f"tile_{col}_{row}.jpg")
                        tile.save(tile_path)
            else:
                # print(f"Not saving blank tile at column {col} and row {row}")
                pass


    print("paleoooo")
    weights_path = "/app/darknet/yolov4-tiny.weights"
    config_path = "/app/darknet/yolov4-tiny.cfg"


    net = cv2.dnn.readNet(weights_path, config_path)

    # Define the output layers of the network
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

    # Define the input folder and output folder
    input_folder = "/app/paleo_images"
    
    output_folder = "/app/paleo_images_wo_blank"

    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
       os.makedirs(output_folder)
    
    #tile_list_wo_blank = []

    for filename in os.listdir(input_folder):
        if filename.endswith(".jpg"):
            # Load the image and get its dimensions
            img = cv2.imread(os.path.join(input_folder, filename))

            
            height, width, channels = img.shape
            #print( img.shape)

            # Create a blob from the image and feed it forward through the network
            blob = cv2.dnn.blobFromImage(img, 1/255, (416, 416), swapRB=True, crop=False)
            net.setInput(blob)
            detections = net.forward(output_layers)

            # Loop through each detection and save the image if it contains an object of interest
            has_image = False
            for detection in detections[0]:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if class_id == 0 and confidence > 0.2:   # The confidence can be varied to include or remove more images
                    has_image = True
                    break

            if has_image:
                # Check if the image is blank
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                if np.mean(gray) > 10:
                    output_filepath = os.path.join(output_folder, 'img_'+str(filename)+'.jpg')
                    cv2.imwrite(output_filepath, img)
    
    print("paleoooo 22222")

    
    


    # Set the path to the input folder containing the tiled images
    input_folder_path = "/app/paleo_images_wo_blank"

    # Set the path to the output folder where the segmented images will be saved
    output_folder_path = "/app/watershed_images"

    # Create the output folder if it does not exist
    if not os.path.exists(output_folder_path):
       os.makedirs(output_folder_path)

    


    

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
    
    return print("paleoooo 3333")
        
   

process_images(slide)

