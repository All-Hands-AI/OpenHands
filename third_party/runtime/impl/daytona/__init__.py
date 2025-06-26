"""Daytona runtime implementation.

This runtime reads configuration directly from environment variables:
- DAYTONA_API_KEY: API key for Daytona authentication
- DAYTONA_API_URL: Daytona API URL endpoint (defaults to https://app.daytona.io/api)
- DAYTONA_TARGET: Daytona target region (defaults to 'eu')
"""