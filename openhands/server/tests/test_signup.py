import pytest
import requests
from eth_account import Account
from eth_account.messages import encode_defunct


@pytest.fixture
def eth_account():
    """Fixture to create a test Ethereum account"""
    Account.enable_unaudited_hdwallet_features()
    acct = Account.create()
    return {'private_key': acct.key.hex(), 'public_address': acct.address}


@pytest.fixture
def signed_message(eth_account):
    """Fixture to create a signed authentication message"""
    message = 'Sign this message to authenticate with OpenHands'
    message_hash = encode_defunct(text=message)
    signed = Account.sign_message(message_hash, eth_account['private_key'])
    return signed.signature.hex()


def test_signup_endpoint(eth_account, signed_message):
    """Test the signup API endpoint"""
    # Arrange
    url = 'http://localhost:3000/api/auth/signup'
    payload = {
        'publicAddress': eth_account['public_address'],
        'signature': signed_message,
    }
    headers = {'Content-Type': 'application/json'}

    # Act
    response = requests.post(url, json=payload, headers=headers)

    # Assert
    assert (
        response.status_code == 200
    ), f'Expected status code 200, got {response.status_code}. Response: {response.text}'

    response_data = response.json()
    assert 'token' in response_data, 'Response should contain a JWT token'
    assert 'user' in response_data, 'Response should contain user information'
    assert (
        response_data['user']['publicAddress'].lower()
        == eth_account['public_address'].lower()
    ), 'Public address in response should match the request'
