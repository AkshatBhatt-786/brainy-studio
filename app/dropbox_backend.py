import dropbox
import re
from datetime import datetime, timedelta
from dropbox.exceptions import ApiError, AuthError, BadInputError, InternalServerError
from dropbox.files import WriteMode
from icecream import ic

class DropboxBackend:

    def __init__(self, refresh_token: str, app_key: str, app_secret: str, root_path: str):
        self.dbx = dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret
        )
        self.root_path = root_path
        
    @staticmethod
    def handle_error(e):
        if isinstance(e, AuthError):
            ic("Authentication error. Please check your access token.")
        elif isinstance(e, ApiError):
            ic(f"API error: {e}")
        elif isinstance(e, BadInputError):
            ic("Bad input error. Please verify your inputs.")
        elif isinstance(e, InternalServerError):
            ic("Internal server error. Please try again later.")
        else:
            ic(f"An unexpected error occurred: {e}")

    def lists_files(self, folder_path):
        dropbox_files = []
        try:
            files = self.dbx.files_list_folder(folder_path)
            for entry in files.entries:
                print(f"File: {entry.name}")
                dropbox_files.append(entry.name)
            return dropbox_files
        except Exception as e:
            ic(f"Failed to find folder path: {folder_path}.")
            print(e)
            return None

    def download_file(self, dropbox_path: str, local_path: str):
        try:
            metadata, res = self.dbx.files_download(dropbox_path)
            with open(local_path, "wb") as f:
                f.write(res.content)
            ic(f"Downloaded {dropbox_path} to {local_path}")
            return True
        except ApiError as e:
            if e.error.is_path() and e.error.get_path().is_not_found():
                ic(f"File '{dropbox_path}' not found in Dropbox.")
            else:
                ic(f"API error during download: {e}")
            return False
        except PermissionError:
            ic(f"Permission denied: Unable to write to '{local_path}'.")
            return False
        except Exception as e:
            ic(f"An unexpected error occurred during file download: {e}")
            return False

    def upload_file(self, local_path: str, dropbox_path: str):
        try:
            with open(local_path, "rb") as f:
                self.dbx.files_upload(f.read(), dropbox_path, mode=WriteMode("overwrite"))
                return True
        except FileNotFoundError:
            ic(f"Local file '{local_path}' not found.")
            return False
        except ApiError as e:
            if e.error.is_path() and e.error.get_path():
                ic(f"Conflict error: File '{dropbox_path}' already exists.")
                return False
            else:
                ic(f"API error during upload: {e}")
                return False
        except Exception as e:
            ic(f"An unexpected error occurred during file upload: {e}")
            return False

    def delete_file(self, dropbox_path):
        try:
            self.dbx.files_delete_v2(dropbox_path)
            ic(f"File: {dropbox_path} deleted successfully!")
            return True
        except dropbox.exceptions.ApiError as e:
            if e.error.is_path_lookup() and e.error.get_path_lookup().is_not_found():
                ic(f"Error: File '{dropbox_path}' not found in Dropbox.")
                return False
            else:
                ic(f"API error during file deletion: {e}")
                return False
        except Exception as e:
            ic(f"An unexpected error occurred while deleting the file: {e}")
            return False

