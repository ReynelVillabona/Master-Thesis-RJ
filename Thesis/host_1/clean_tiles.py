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
import glob
from openslide.deepzoom import DeepZoomGenerator
import cv2


mrxs_file_path = glob.glob("/app/*.mrxs")[0]
slide = openslide.OpenSlide(mrxs_file_path)
    



def clean_tiles(slide):
    
    
    json_file_path = '/app/values.json'
    with open(json_file_path, 'r') as f:
        data = json.load(f)
        resolution = data['resolution']
        zoom = data['zoom']
    
    tiles = DeepZoomGenerator(slide, tile_size=resolution, overlap=0, limit_bounds=False)
    

    level_num= zoom
    level_tiles_tot = tiles.level_tiles[level_num][0]*tiles.level_tiles[level_num][1]
    
    folder_path = "/app/paleo_images"
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    Idx_max = zoom
    
    count_paleo_images = 0
    
    

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
                        count_paleo_images += 1
            else:
                # print(f"Not saving blank tile at column {col} and row {row}")
                pass


        
    
    return json.dumps({"Tiles": count_paleo_images, "Total_tiles": level_tiles_tot, "resolution": resolution, "zoom": zoom, })

output = clean_tiles(slide)
print(output)
