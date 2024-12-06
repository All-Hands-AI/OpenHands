from typing import List

from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from openhands.core.logger import openhands_logger as logger


class GoogleSheetsClient:
    def __init__(self):
        """Initialize Google Sheets client using workload identity.
        Uses application default credentials which supports workload identity when running in GCP.
        """
        logger.info('Initializing Google Sheets client with workload identity')
        try:
            credentials, project = default(
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            logger.info(f'Successfully obtained credentials for project: {project}')
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info('Successfully initialized Google Sheets API service')
        except Exception as e:
            logger.error(f'Failed to initialize Google Sheets client: {str(e)}')
            self.service = None

    def get_usernames(self, spreadsheet_id: str, range_name: str = 'A:A') -> List[str]:
        """Get list of usernames from specified Google Sheet.

        Args:
            spreadsheet_id: The ID of the Google Sheet
            range_name: The A1 notation of the range to fetch

        Returns:
            List of usernames from the sheet
        """
        if not self.service:
            logger.error('Google Sheets service not initialized')
            return []

        try:
            logger.info(
                f'Fetching usernames from sheet {spreadsheet_id}, range {range_name}'
            )
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )

            values = result.get('values', [])
            usernames = [
                str(cell[0]).strip() for cell in values if cell and cell[0].strip()
            ]
            logger.info(
                f'Successfully fetched {len(usernames)} usernames from Google Sheet'
            )
            return usernames

        except HttpError as err:
            logger.error(f'Error accessing Google Sheet {spreadsheet_id}: {err}')
            return []
        except Exception as e:
            logger.error(
                f'Unexpected error accessing Google Sheet {spreadsheet_id}: {str(e)}'
            )
            return []
