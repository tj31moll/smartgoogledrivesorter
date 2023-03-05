import os
import shutil
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
import base64
import numpy as np
from keras.preprocessing.image import img_to_array
from keras.applications.resnet50 import preprocess_input
from keras.applications.resnet50 import decode_predictions
import requests
from PIL import Image

# enter your own Google API credentials here
creds = Credentials.from_authorized_user_file('credentials.json', ['https://www.googleapis.com/auth/drive'])

# enter the ID of the folder you want to sort here
folder_id = 'your_folder_id_here'

# load the pre-trained ResNet50 model
model = ResNet50(weights='imagenet')

def classify_file(item):
    """Classify a file based on its content and return the ID of the corresponding folder."""
    if item['mimeType'].startswith('image/'):
        # classify image files using ResNet50
        file_url = f'https://drive.google.com/uc?id={item["id"]}'
        response = requests.get(file_url)
        img = Image.open(io.BytesIO(response.content))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        preds = model.predict(img_array)
        top_preds = decode_predictions(preds, top=1)[0]
        file_type_folder = [f['id'] for f in items if f['name'] == top_preds[0][1]][0]
    else:
        # move non-image files into the folder that corresponds to their file type
        file_type_folder = [f['id'] for f in items if f['mimeType'] == item['mimeType']][0]
    return file_type_folder

def main():
    # create a Google Drive API client
    service = build('drive', 'v3', credentials=creds)
    
    # get all the files in the specified folder
    results = service.files().list(q="parents='" + folder_id + "' and trashed = false",fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])
    
    # create folders for each file type
    file_types = set([item['mimeType'] for item in items])
    for file_type in file_types:
        if file_type != 'application/vnd.google-apps.folder':
            try:
                service.files().create(
                    body={'name': file_type, 'parents': [folder_id], 'mimeType': 'application/vnd.google-apps.folder'}
                ).execute()
            except HttpError as error:
                print(f'An error occurred while creating the {file_type} folder: {error}')
    
    # move files into their respective folders
    for item in items:
        if item['mimeType'] != 'application/vnd.google-apps.folder':
            file_type_folder = classify_file(item)
            try:
                service.files().update(
                    fileId=item['id'],
                    addParents=file_type_folder,
                    removeParents=item['parents'][0],
                    fields='id, parents'
                ).execute()
            except HttpError as error:
                print(f'An error occurred while moving {item["name"]}: {error}')

if __name__ == '__main__':
    main()
