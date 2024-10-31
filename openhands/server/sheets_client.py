from typing import List, Optional
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsClient:
    def __init__(self, credentials_path: str):
        """Initialize Google Sheets client with service account credentials.
        
        Args:
            credentials_path: Path to the service account JSON credentials file
        """
        self.credentials = None
        self.service = None
        if os.path.exists(credentials_path):
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=self.credentials)

    def get_usernames(self, spreadsheet_id: str, range_name: str = 'A:A') -> List[str]:
        """Get list of usernames from specified Google Sheet.
        
        Args:
            spreadsheet_id: The ID of the Google Sheet
            range_name: The A1 notation of the range to fetch
            
        Returns:
            List of usernames from the sheet
        """
        if not self.service:
            return []
            
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            # Flatten the list and remove empty strings
            return [str(cell[0]).strip() for cell in values if cell and cell[0].strip()]
            
        except HttpError as err:
            print(f"Error accessing Google Sheet: {err}")
            return []