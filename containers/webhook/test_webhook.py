#!/usr/bin/env python3
"""
Test script for the GitHub webhook endpoint.
This script simulates a GitHub webhook event for a pull request.
"""

import argparse
import hmac
import json
import sys
from urllib.request import Request, urlopen

# Sample PR payload based on GitHub's webhook format
SAMPLE_PR_PAYLOAD = {
    "action": "opened",
    "pull_request": {
        "number": 123,
        "title": "Test PR for webhook",
        "body": "This is a test PR to verify webhook functionality",
        "head": {
            "ref": "feature-branch"
        },
        "base": {
            "ref": "main"
        }
    },
    "repository": {
        "full_name": "test-org/test-repo"
    },
    "sender": {
        "login": "test-user"
    }
}

def main():
    parser = argparse.ArgumentParser(description="Test the GitHub webhook endpoint")
    parser.add_argument("--url", default="http://localhost:8000/api/webhooks/github",
                        help="Webhook URL (default: http://localhost:8000/api/webhooks/github)")
    parser.add_argument("--secret", default="",
                        help="Webhook secret for signature verification")
    args = parser.parse_args()

    # Convert payload to JSON
    payload_bytes = json.dumps(SAMPLE_PR_PAYLOAD).encode('utf-8')
    
    # Create headers
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "pull_request",
        "User-Agent": "GitHub-Hookshot/test"
    }
    
    # Add signature if secret is provided
    if args.secret:
        signature = hmac.new(
            args.secret.encode(),
            msg=payload_bytes,
            digestmod="sha256"
        ).hexdigest()
        headers["X-Hub-Signature-256"] = f"sha256={signature}"
    
    # Create request
    request = Request(
        args.url,
        data=payload_bytes,
        headers=headers,
        method="POST"
    )
    
    # Send request
    try:
        with urlopen(request) as response:
            response_body = response.read().decode('utf-8')
            print(f"Response status: {response.status}")
            print(f"Response body: {response_body}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()