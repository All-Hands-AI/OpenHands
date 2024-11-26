# OpenHands Analytics Documentation

This document describes the user flow and analytics tracking in OpenHands.

## User Entry Points

Users can enter the application through multiple paths:

1. Direct Query Entry
   - User enters query directly in hero page
   - Event: `initial_query_submitted`
   - Properties:
     - `query_character_length`: Length of the query

2. GitHub Repository Selection
   - User selects a GitHub repository first
   - Event: `repository_selected`
   - Properties:
     - `repository_name`: Name of the selected repository
     - `repository_owner`: Owner of the repository

3. ZIP File Upload
   - User uploads a ZIP file containing code
   - Event: `zip_file_uploaded`
   - Properties:
     - `file_name`: Name of the uploaded file
     - `file_size`: Size of the file in bytes

## Chat Flow

After entering through any of the above paths:

1. First Message
   - User sends their first message after repo selection/upload
   - Event: `first_message_after_context`
   - Properties:
     - `entry_point`: How user entered ("direct", "github", "zip")
     - `message_length`: Length of the message
     - `has_repository`: Whether a repository was selected
     - `has_files`: Whether files were uploaded

2. Regular Messages
   - User sends subsequent messages
   - Event: `user_message_sent`
   - Properties:
     - `current_message_count`: Number of messages in the conversation

## Project Actions

1. Project Menu Card: GitHub Integration
   - User pushes changes to GitHub
   - Event: `push_to_github_button_clicked`

2. Project Menu Card: Workspace Download
   - User downloads workspace as ZIP
   - Event: `download_workspace_button_clicked`

3. Chat Interface: Push to Branch
   - Event: `push_to_branch_button_clicked`

4. Chat Interface: Create PR
   - Event: `create_pr_button_clicked`

5. Chat Interface: Push changes to PR
   - Event: `push_to_pr_button_clicked`

6. Stop Action
   - User stops the agent
   - Event: `stop_button_clicked`
