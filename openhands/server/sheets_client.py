from typing import List
from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetsClient:
    def __init__(self):
        """Initialize Google Sheets client using workload identity.
        Uses application default credentials which supports workload identity when running in GCP.
        """
        credentials, _ = default(scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
        self.service = build('sheets', 'v4', credentials=credentials)

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