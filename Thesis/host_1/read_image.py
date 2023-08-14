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

mrxs_file_path = glob.glob("/app/*.mrxs")[0]
slide = openslide.OpenSlide(mrxs_file_path)

def read_image(slide):
    
        
    factors = slide.level_downsamples
    
    
      
    tiles = DeepZoomGenerator(slide, tile_size=factors[0], overlap=0, limit_bounds=False)
    num_deepzoom_levels = tiles.level_count

    level_num= num_deepzoom_levels-1
    level_tiles_tot = tiles.level_tiles[level_num][0]*tiles.level_tiles[level_num][1]

    slide.close()

    return json.dumps({"factors": factors, "num_deepzoom_levels": num_deepzoom_levels, "Tiles_totales": level_tiles_tot})

output = read_image(slide)
print(output)