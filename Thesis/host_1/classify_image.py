import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from keras.models import load_model
import json
import glob
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Specify the path to the image file and the desired size
image_files = glob.glob("/app/*.png") + glob.glob("/app/*.jpg")
if image_files:
    image_path = image_files[0] 


h5_file_path = glob.glob("/app/*.h5")[0]
model = load_model(h5_file_path)

desired_size = (224, 224)

def resize_image(image_path, desired_size):
  # Check if the image file exists
  if not os.path.exists(image_path):
    return None
    
  # Load the image using OpenCV
  image = cv2.imread(image_path)
        
   # Check if the image is loaded successfully
  if image is None:
    return None
  # Resize the image
  resized_image = cv2.resize(image, desired_size)
  # Convert the resized image to RGB format
  resized_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)
  # Get the model's class indices
  model_class_indices = model.predict(np.zeros((1, 224, 224, 3))).argmax(axis=1)
  # Define the class labels
  class_labels = [
            'Acanthaulax venusta',
            'Cribroperidinium "prominoseptatum"',
            'Dingodinium tuberculosum',
            'Dingodinium tuberosum',
            'Fibrocysta axialis',
            'Gonyaulacysta jurassica',
            'Palaeoperidinium pyrophorum',
            'Senoniasphaera inornata',
            'Sentusidinium pilosum',
            'Spongodinium delitiense',
            'Spongodinium delitiense (operculum)',
            'Systematophora areolata',
            'Tubotuberella apatela'
        ]
  # Create a dictionary mapping the model's class indices to the class labels
  class_mapping = {index: label for index, label in enumerate(class_labels)}
  
    
  # Preprocess the image
  preprocessed_image = np.expand_dims(resized_image, axis=0)
  preprocessed_image = preprocessed_image / 255.0  # Normalize pixel values to the range [0, 1]

  # Perform the prediction
  predictions = model.predict(preprocessed_image)

  # Get the predicted class label
  predicted_class_index = np.argmax(predictions[0])

  # Print the predicted class index
        

  predicted_class_label = class_labels[predicted_class_index]
  
  return json.dumps({"predicted_class_label": predicted_class_label })
    
    

output = resize_image(image_path, desired_size)
print(output)