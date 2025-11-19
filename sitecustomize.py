"""
Site customization to disable SSL verification for all Python SSL connections.
This is used in environments with SSL/TLS inspection.
WARNING: This disables SSL verification globally and should only be used in controlled environments.
"""
import ssl
import os

# Disable SSL verification globally
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

# Set environment variables for requests library
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
