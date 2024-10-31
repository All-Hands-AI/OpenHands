# Setting up Google Sheets Integration

To use the Google Sheets integration for GitHub user verification, follow these steps:

1. Add the required dependencies to your project:
```bash
poetry add google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

2. Set up environment variables:
```bash
# Existing variables
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_USER_LIST_FILE=/path/to/users.txt  # Optional: Keep for backwards compatibility

# New variables for Google Sheets
GOOGLE_CREDENTIALS_FILE=/path/to/service-account-credentials.json
GITHUB_USERS_SHEET_ID=your_google_sheet_id
```

3. Create a Google Cloud Project and enable the Google Sheets API:
   - Go to Google Cloud Console
   - Create a new project or select an existing one
   - Enable the Google Sheets API
   - Create a service account and download the JSON credentials
   - Save the credentials file securely and set its path in GOOGLE_CREDENTIALS_FILE

4. Set up your Google Sheet:
   - Create a new Google Sheet
   - Share it with the service account email (found in the credentials JSON)
   - Put GitHub usernames in column A
   - Copy the Sheet ID from the URL (the long string between /d/ and /edit)
   - Set the Sheet ID in GITHUB_USERS_SHEET_ID

The system will now check both the text file (if configured) and Google Sheet for valid GitHub usernames. A user will be allowed if they appear in either source.