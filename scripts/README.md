# OpenHands Scripts

This directory contains utility scripts for maintaining the OpenHands project.

## update_openapi.py

Updates the OpenAPI documentation by generating it from the FastAPI application.

### Usage

```bash
python scripts/update_openapi.py
```

### What it does

1. Generates the OpenAPI specification from the live FastAPI application
2. Preserves server configuration from the existing documentation
3. Updates the API version to match the package version
4. Creates a backup of the current documentation
5. Writes the updated specification to `docs/openapi.json`

### When to run

- After adding new API endpoints
- After modifying existing endpoint signatures
- After changing response models or request schemas
- Before releasing a new version
- When the API documentation appears out of date

### Output

The script will show:
- Total number of endpoints documented
- OpenAPI specification version
- API version
- Sample endpoints

### Automation

Consider running this script as part of your CI/CD pipeline or pre-commit hooks to ensure the API documentation stays up to date.
