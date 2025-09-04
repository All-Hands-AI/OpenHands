#!/usr/bin/env python3
"""Sync script to add Keycloak users to Resend.com audience.

This script uses the Keycloak admin client to fetch users and adds them to a
Resend.com audience. It handles rate limiting and retries with exponential
backoff for adding contacts. When a user is newly added to the mailing list, a welcome email is sent.

Required environment variables:
- KEYCLOAK_SERVER_URL: URL of the Keycloak server
- KEYCLOAK_REALM_NAME: Keycloak realm name
- KEYCLOAK_ADMIN_PASSWORD: Password for the Keycloak admin user
- RESEND_API_KEY: API key for Resend.com
- RESEND_AUDIENCE_ID: ID of the Resend audience to add users to

Optional environment variables:
- KEYCLOAK_PROVIDER_NAME: Provider name for Keycloak
- KEYCLOAK_CLIENT_ID: Client ID for Keycloak
- KEYCLOAK_CLIENT_SECRET: Client secret for Keycloak
- RESEND_FROM_EMAIL: Email address to use as the sender (default: "All Hands Team <contact@all-hands.dev>")
- BATCH_SIZE: Number of users to process in each batch (default: 100)
- MAX_RETRIES: Maximum number of retries for API calls (default: 3)
- INITIAL_BACKOFF_SECONDS: Initial backoff time for retries (default: 1)
- MAX_BACKOFF_SECONDS: Maximum backoff time for retries (default: 60)
- BACKOFF_FACTOR: Backoff factor for retries (default: 2)
- RATE_LIMIT: Rate limit for API calls (requests per second) (default: 2)
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional

import resend
from keycloak.exceptions import KeycloakError
from resend.exceptions import ResendError
from server.auth.token_manager import get_keycloak_admin
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from openhands.core.logger import openhands_logger as logger

# Get Keycloak configuration from environment variables
KEYCLOAK_SERVER_URL = os.environ.get('KEYCLOAK_SERVER_URL', '')
KEYCLOAK_REALM_NAME = os.environ.get('KEYCLOAK_REALM_NAME', '')
KEYCLOAK_PROVIDER_NAME = os.environ.get('KEYCLOAK_PROVIDER_NAME', '')
KEYCLOAK_CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', '')
KEYCLOAK_CLIENT_SECRET = os.environ.get('KEYCLOAK_CLIENT_SECRET', '')
KEYCLOAK_ADMIN_PASSWORD = os.environ.get('KEYCLOAK_ADMIN_PASSWORD', '')

# Logger is imported from openhands.core.logger

# Get configuration from environment variables
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
RESEND_AUDIENCE_ID = os.environ.get('RESEND_AUDIENCE_ID', '')

# Sync configuration
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '100'))
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
INITIAL_BACKOFF_SECONDS = float(os.environ.get('INITIAL_BACKOFF_SECONDS', '1'))
MAX_BACKOFF_SECONDS = float(os.environ.get('MAX_BACKOFF_SECONDS', '60'))
BACKOFF_FACTOR = float(os.environ.get('BACKOFF_FACTOR', '2'))
RATE_LIMIT = float(os.environ.get('RATE_LIMIT', '2'))  # Requests per second

# Set up Resend API
resend.api_key = RESEND_API_KEY

print('resend module', resend)
print('has contacts', hasattr(resend, 'Contacts'))


class ResendSyncError(Exception):
    """Base exception for Resend sync errors."""

    pass


class KeycloakClientError(ResendSyncError):
    """Exception for Keycloak client errors."""

    pass


class ResendAPIError(ResendSyncError):
    """Exception for Resend API errors."""

    pass


def get_keycloak_users(offset: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """Get users from Keycloak using the admin client.

    Args:
        offset: The offset to start from.
        limit: The maximum number of users to return.

    Returns:
        A list of users.

    Raises:
        KeycloakClientError: If the API call fails.
    """
    try:
        keycloak_admin = get_keycloak_admin()

        # Get users with pagination
        # The Keycloak API uses 'first' for offset and 'max' for limit
        params: Dict[str, Any] = {
            'first': offset,
            'max': limit,
            'briefRepresentation': False,  # Get full user details
        }

        users_data = keycloak_admin.get_users(params)
        logger.info(f'Fetched {len(users_data)} users from Keycloak')

        # Transform the response to match our expected format
        users = []
        for user in users_data:
            if user.get('email'):  # Ensure user has an email
                users.append(
                    {
                        'id': user.get('id'),
                        'email': user.get('email'),
                        'first_name': user.get('firstName'),
                        'last_name': user.get('lastName'),
                        'username': user.get('username'),
                    }
                )

        return users
    except KeycloakError:
        logger.exception('Failed to get users from Keycloak')
        raise
    except Exception:
        logger.exception('Unexpected error getting users from Keycloak')
        raise


def get_total_keycloak_users() -> int:
    """Get the total number of users in Keycloak.

    Returns:
        The total number of users.

    Raises:
        KeycloakClientError: If the API call fails.
    """
    try:
        keycloak_admin = get_keycloak_admin()
        count = keycloak_admin.users_count()
        return count
    except KeycloakError:
        logger.exception('Failed to get total users from Keycloak')
        raise
    except Exception:
        logger.exception('Unexpected error getting total users from Keycloak')
        raise


def get_resend_contacts(audience_id: str) -> Dict[str, Dict[str, Any]]:
    """Get contacts from Resend.

    Args:
        audience_id: The Resend audience ID.

    Returns:
        A dictionary mapping email addresses to contact data.

    Raises:
        ResendAPIError: If the API call fails.
    """
    print('getting resend contacts')
    print('has resend contacts', hasattr(resend, 'Contacts'))
    try:
        contacts = resend.Contacts.list(audience_id).get('data', [])
        # Create a dictionary mapping email addresses to contact data for
        # efficient lookup
        return {contact['email'].lower(): contact for contact in contacts}
    except Exception:
        logger.exception('Failed to get contacts from Resend')
        raise


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(
        multiplier=INITIAL_BACKOFF_SECONDS,
        max=MAX_BACKOFF_SECONDS,
        exp_base=BACKOFF_FACTOR,
    ),
    retry=retry_if_exception_type((ResendError, KeycloakClientError)),
)
def add_contact_to_resend(
    audience_id: str,
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a contact to the Resend audience with retry logic.

    Args:
        audience_id: The Resend audience ID.
        email: The email address of the contact.
        first_name: The first name of the contact.
        last_name: The last name of the contact.

    Returns:
        The API response.

    Raises:
        ResendAPIError: If the API call fails after retries.
    """
    try:
        params = {'audience_id': audience_id, 'email': email}

        if first_name:
            params['first_name'] = first_name

        if last_name:
            params['last_name'] = last_name

        return resend.Contacts.create(params)
    except Exception:
        logger.exception(f'Failed to add contact {email} to Resend')
        raise


def send_welcome_email(
    email: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Send a welcome email to a new contact.

    Args:
        email: The email address of the contact.
        first_name: The first name of the contact.
        last_name: The last name of the contact.

    Returns:
        The API response.

    Raises:
        ResendError: If the API call fails.
    """
    try:
        # Prepare the recipient name
        recipient_name = ''
        if first_name:
            recipient_name = first_name
            if last_name:
                recipient_name += f' {last_name}'

        # Personalize greeting based on available information
        greeting = f'Hi {recipient_name},' if recipient_name else 'Hi there,'

        # Prepare email parameters
        params = {
            'from': os.environ.get(
                'RESEND_FROM_EMAIL', 'All Hands Team <contact@all-hands.dev>'
            ),
            'to': [email],
            'subject': 'Welcome to OpenHands Cloud',
            'html': f"""
            <div>
                <p>{greeting}</p>
                <p>Thanks for joining OpenHands Cloud — we're excited to help you start building with the world's leading open source AI coding agent!</p>
                <p><strong>Here are three quick ways to get started:</strong></p>
                <ol>
                    <li><a href="https://docs.all-hands.dev/usage/cloud/openhands-cloud#next-steps"><strong>Connect your Git repo</strong></a> – Link your <a href="https://docs.all-hands.dev/usage/cloud/github-installation">GitHub</a> or <a href="https://docs.all-hands.dev/usage/cloud/gitlab-installation">GitLab</a> repository in seconds so OpenHands can begin understanding your codebase and suggest tasks.</li>
                    <li><a href="https://docs.all-hands.dev/usage/cloud/github-installation#working-on-github-issues-and-pull-requests-using-openhands"><strong>Use OpenHands on an issue or pull request</strong></a> – Label an issue with 'openhands' or mention @openhands on any PR comment to generate explanations, tests, refactors, or doc fixes tailored to the exact lines you're reviewing.</li>
                    <li><a href="https://join.slack.com/t/openhands-ai/shared_invite/zt-34zm4j0gj-Qz5kRHoca8DFCbqXPS~f_A"><strong>Join the community</strong></a> – Drop into our Slack Community to share tips, feedback, and help shape the next features on our roadmap.</li>
                </ol>
                <p>Have questions? Want to share feedback? Just reply to this email—we're here to help.</p>
                <p>Happy coding!</p>
                <p>The All Hands AI team</p>
            </div>
            """,
        }

        # Send the email
        response = resend.Emails.send(params)
        logger.info(f'Welcome email sent to {email}')
        return response
    except Exception:
        logger.exception(f'Failed to send welcome email to {email}')
        raise


def sync_users_to_resend():
    """Sync users from Keycloak to Resend."""
    # Check required environment variables
    required_vars = {
        'RESEND_API_KEY': RESEND_API_KEY,
        'RESEND_AUDIENCE_ID': RESEND_AUDIENCE_ID,
        'KEYCLOAK_SERVER_URL': KEYCLOAK_SERVER_URL,
        'KEYCLOAK_REALM_NAME': KEYCLOAK_REALM_NAME,
        'KEYCLOAK_ADMIN_PASSWORD': KEYCLOAK_ADMIN_PASSWORD,
    }

    missing_vars = [var for var, value in required_vars.items() if not value]

    if missing_vars:
        for var in missing_vars:
            logger.error(f'{var} environment variable is not set')
        sys.exit(1)

    # Log configuration (without sensitive info)
    logger.info(f'Using Keycloak server: {KEYCLOAK_SERVER_URL}')
    logger.info(f'Using Keycloak realm: {KEYCLOAK_REALM_NAME}')

    logger.info(
        f'Starting sync of Keycloak users to Resend audience {RESEND_AUDIENCE_ID}'
    )

    try:
        # Get the total number of users
        total_users = get_total_keycloak_users()
        logger.info(
            f'Found {total_users} users in Keycloak realm {KEYCLOAK_REALM_NAME}'
        )

        # Get contacts from Resend
        resend_contacts = get_resend_contacts(RESEND_AUDIENCE_ID)
        logger.info(
            f'Found {len(resend_contacts)} contacts in Resend audience '
            f'{RESEND_AUDIENCE_ID}'
        )

        # Stats
        stats = {
            'total_users': total_users,
            'existing_contacts': len(resend_contacts),
            'added_contacts': 0,
            'errors': 0,
        }

        # Process users in batches
        offset = 0
        while offset < total_users:
            users = get_keycloak_users(offset, BATCH_SIZE)
            logger.info(f'Processing batch of {len(users)} users (offset {offset})')

            for user in users:
                email = user.get('email')
                if not email:
                    continue

                email = email.lower()
                if email in resend_contacts:
                    logger.debug(f'User {email} already exists in Resend, skipping')
                    continue

                try:
                    first_name = user.get('first_name')
                    last_name = user.get('last_name')

                    # Add the contact to the Resend audience
                    add_contact_to_resend(
                        RESEND_AUDIENCE_ID, email, first_name, last_name
                    )
                    logger.info(f'Added user {email} to Resend')
                    stats['added_contacts'] += 1

                    # Sleep to respect rate limit after first API call
                    time.sleep(1 / RATE_LIMIT)

                    # Send a welcome email to the newly added contact
                    try:
                        send_welcome_email(email, first_name, last_name)
                        logger.info(f'Sent welcome email to {email}')
                    except Exception:
                        logger.exception(
                            f'Failed to send welcome email to {email}, but contact was added to audience'
                        )
                        # Continue with the sync process even if sending the welcome email fails

                    # Sleep to respect rate limit after second API call
                    time.sleep(1 / RATE_LIMIT)
                except Exception:
                    logger.exception(f'Error adding user {email} to Resend')
                    stats['errors'] += 1

            offset += BATCH_SIZE

        logger.info(f'Sync completed: {stats}')
    except KeycloakClientError:
        logger.exception('Keycloak client error')
        sys.exit(1)
    except ResendAPIError:
        logger.exception('Resend API error')
        sys.exit(1)
    except Exception:
        logger.exception('Sync failed with unexpected error')
        sys.exit(1)


if __name__ == '__main__':
    sync_users_to_resend()
