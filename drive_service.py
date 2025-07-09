
import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_NAME = "StudyMaterialManager"

class DriveService:
    def __init__(self, credentials_file='credentials.json'):
        self.credentials_file = credentials_file
        self.creds = self._get_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)
        self.folder_id = self._get_or_create_folder()

    def _get_credentials(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def _get_or_create_folder(self):
        """Check if 'StudyMaterialManager' folder exists and return its ID, or create it."""
        response = self.service.files().list(
            q=f"name='{FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        if response.get('files'):
            return response.get('files')[0].get('id')
        else:
            file_metadata = {
                'name': FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')

    def upload_file(self, file_path, file_name):
        file_metadata = {
            'name': file_name,
            'parents': [self.folder_id]
        }
        media = MediaFileUpload(file_path, mimetype='application/octet-stream')
        file = self.service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        return file.get('id')

    def download_file(self, file_id, destination_path):
        request = self.service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%.")
        return destination_path

    def get_file_name(self, file_id):
        file_metadata = self.service.files().get(fileId=file_id, fields='name').execute()
        return file_metadata.get('name')
