---
name: Secrets Management
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - secrets management
  - manage secrets
  - secure credentials
  - password management
  - api keys
  - environment variables
  - aws secrets manager
  - vault
  - keychain
  - credential storage
---

# Secrets Management Microagent

This microagent provides guidance on securely managing sensitive information such as API keys, passwords, and other credentials.

## Capabilities

- Store and retrieve secrets securely
- Manage environment variables
- Work with various secrets management tools
- Implement best practices for secrets handling
- Integrate with cloud-based secrets managers
- Secure local development environments

## Secrets Management Options

### Environment Variables

Environment variables are a simple way to store secrets, but they have limitations:

```bash
# Set environment variables
export API_KEY="your_api_key_here"
export DB_PASSWORD="your_password_here"

# Access environment variables in code
api_key = os.environ.get("API_KEY")
db_password = os.environ.get("DB_PASSWORD")
```

For persistence, add to shell profile:
```bash
echo 'export API_KEY="your_api_key_here"' >> ~/.bashrc
echo 'export DB_PASSWORD="your_password_here"' >> ~/.bashrc
source ~/.bashrc
```

### .env Files

Store secrets in a .env file (never commit to version control):

```
# .env file
API_KEY=your_api_key_here
DB_PASSWORD=your_password_here
```

Load in Python with python-dotenv:
```python
from dotenv import load_dotenv
load_dotenv()

import os
api_key = os.environ.get("API_KEY")
db_password = os.environ.get("DB_PASSWORD")
```

### AWS Secrets Manager

For cloud-based applications, AWS Secrets Manager provides a secure way to store and retrieve secrets:

```python
import boto3
import json

def get_secret(secret_name, region_name="us-east-1"):
    """Retrieve a secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name=region_name)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
        else:
            return response['SecretBinary']
    except Exception as e:
        print(f"Error retrieving secret: {e}")
        return None

def store_secret(secret_name, secret_value, region_name="us-east-1"):
    """Store a secret in AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name=region_name)
    
    try:
        if isinstance(secret_value, dict):
            secret_value = json.dumps(secret_value)
            
        response = client.create_secret(
            Name=secret_name,
            SecretString=secret_value
        )
        return response
    except client.exceptions.ResourceExistsException:
        response = client.update_secret(
            SecretId=secret_name,
            SecretString=secret_value
        )
        return response
    except Exception as e:
        print(f"Error storing secret: {e}")
        return None
```

### HashiCorp Vault

For enterprise environments, HashiCorp Vault provides comprehensive secrets management:

```python
import hvac

def get_vault_secret(path, key=None):
    """Retrieve a secret from HashiCorp Vault"""
    client = hvac.Client(url='http://localhost:8200')
    client.token = os.environ.get('VAULT_TOKEN')
    
    try:
        if client.is_authenticated():
            secret = client.secrets.kv.v2.read_secret_version(path=path)
            if key:
                return secret['data']['data'].get(key)
            return secret['data']['data']
        else:
            print("Vault authentication failed")
            return None
    except Exception as e:
        print(f"Error retrieving secret from Vault: {e}")
        return None

def store_vault_secret(path, secret_data):
    """Store a secret in HashiCorp Vault"""
    client = hvac.Client(url='http://localhost:8200')
    client.token = os.environ.get('VAULT_TOKEN')
    
    try:
        if client.is_authenticated():
            client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data
            )
            return True
        else:
            print("Vault authentication failed")
            return False
    except Exception as e:
        print(f"Error storing secret in Vault: {e}")
        return False
```

### System Keychains

For desktop applications, system keychains provide secure storage:

#### macOS Keychain

```python
# Using keyring library (cross-platform)
import keyring

# Store a secret
keyring.set_password("service_name", "username", "password")

# Retrieve a secret
password = keyring.get_password("service_name", "username")
```

#### Windows Credential Manager

```python
# Using keyring library (cross-platform)
import keyring

# Store a secret
keyring.set_password("service_name", "username", "password")

# Retrieve a secret
password = keyring.get_password("service_name", "username")
```

## Best Practices

### General Guidelines

1. **Never hardcode secrets** in source code
2. **Don't store secrets** in version control
3. **Rotate secrets** regularly
4. **Use least privilege** when granting access to secrets
5. **Encrypt secrets** at rest and in transit
6. **Audit access** to sensitive information
7. **Implement secret rotation** policies

### Development Workflow

1. Use `.env` files for local development (add to `.gitignore`)
2. Use environment variables for CI/CD pipelines
3. Use a secrets manager for production environments
4. Implement different secrets for different environments

### Handling Secrets in CI/CD

Most CI/CD platforms provide secure ways to handle secrets:

#### GitHub Actions

```yaml
# GitHub Actions workflow
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Use secret
        env:
          API_KEY: ${{ secrets.API_KEY }}
        run: ./deploy.sh
```

#### GitLab CI

```yaml
# GitLab CI configuration
deploy:
  stage: deploy
  script:
    - ./deploy.sh
  variables:
    API_KEY: $API_KEY
```

## Security Considerations

- **Encryption**: Always encrypt secrets at rest and in transit
- **Access Control**: Implement strict access controls for secrets
- **Monitoring**: Monitor access to secrets and alert on suspicious activity
- **Rotation**: Implement automatic secret rotation
- **Revocation**: Have a process for revoking compromised secrets

## Tool-Specific Guidance

### AWS Secrets Manager

```bash
# Store a secret using AWS CLI
aws secretsmanager create-secret \
    --name MySecret \
    --secret-string '{"username":"admin","password":"password123"}'

# Retrieve a secret using AWS CLI
aws secretsmanager get-secret-value --secret-id MySecret
```

### Docker Secrets

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    image: myapp
    secrets:
      - db_password
secrets:
  db_password:
    file: ./db_password.txt
```

### Kubernetes Secrets

```yaml
# Create a secret
apiVersion: v1
kind: Secret
metadata:
  name: mysecret
type: Opaque
data:
  username: YWRtaW4=  # base64 encoded "admin"
  password: cGFzc3dvcmQxMjM=  # base64 encoded "password123"
```

```yaml
# Use a secret in a pod
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
  - name: mycontainer
    image: myimage
    env:
    - name: DB_USERNAME
      valueFrom:
        secretKeyRef:
          name: mysecret
          key: username
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: mysecret
          key: password
```

## Troubleshooting

### Common Issues

1. **Permission denied**: Check that your application has the necessary permissions to access the secrets
2. **Secret not found**: Verify the secret name and path
3. **Authentication failed**: Check your credentials for the secrets manager
4. **Encryption errors**: Ensure you're using the correct encryption keys

### Debugging Tips

1. Use verbose logging when interacting with secrets managers
2. Check environment variables are correctly set
3. Verify network connectivity to external secrets managers
4. Test access to secrets outside your application

## Example: Complete Secrets Management Utility

```python
#!/usr/bin/env python3
import os
import sys
import json
import argparse
import keyring
import boto3
from dotenv import load_dotenv

class SecretsManager:
    """A utility for managing secrets across different storage backends"""
    
    def __init__(self):
        # Load environment variables from .env file if it exists
        load_dotenv()
    
    def get_secret(self, name, backend="env"):
        """Retrieve a secret from the specified backend"""
        if backend == "env":
            return os.environ.get(name)
        elif backend == "keyring":
            service, username = name.split(":", 1) if ":" in name else (name, "default")
            return keyring.get_password(service, username)
        elif backend == "aws":
            return self._get_aws_secret(name)
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    
    def set_secret(self, name, value, backend="env"):
        """Store a secret in the specified backend"""
        if backend == "env":
            os.environ[name] = value
            return True
        elif backend == "keyring":
            service, username = name.split(":", 1) if ":" in name else (name, "default")
            keyring.set_password(service, username, value)
            return True
        elif backend == "aws":
            return self._set_aws_secret(name, value)
        else:
            raise ValueError(f"Unsupported backend: {backend}")
    
    def _get_aws_secret(self, name, region_name="us-east-1"):
        """Retrieve a secret from AWS Secrets Manager"""
        client = boto3.client('secretsmanager', region_name=region_name)
        
        try:
            response = client.get_secret_value(SecretId=name)
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                return response['SecretBinary']
        except Exception as e:
            print(f"Error retrieving secret from AWS: {e}", file=sys.stderr)
            return None
    
    def _set_aws_secret(self, name, value, region_name="us-east-1"):
        """Store a secret in AWS Secrets Manager"""
        client = boto3.client('secretsmanager', region_name=region_name)
        
        try:
            if isinstance(value, dict):
                value = json.dumps(value)
                
            try:
                response = client.create_secret(
                    Name=name,
                    SecretString=value
                )
            except client.exceptions.ResourceExistsException:
                response = client.update_secret(
                    SecretId=name,
                    SecretString=value
                )
            return True
        except Exception as e:
            print(f"Error storing secret in AWS: {e}", file=sys.stderr)
            return False

def main():
    parser = argparse.ArgumentParser(description="Manage secrets across different storage backends")
    parser.add_argument("action", choices=["get", "set"], help="Action to perform")
    parser.add_argument("name", help="Name of the secret")
    parser.add_argument("--value", help="Value of the secret (for 'set' action)")
    parser.add_argument("--backend", choices=["env", "keyring", "aws"], default="env", 
                        help="Backend to use for storing/retrieving secrets")
    
    args = parser.parse_args()
    
    manager = SecretsManager()
    
    if args.action == "get":
        value = manager.get_secret(args.name, args.backend)
        if value:
            if isinstance(value, dict):
                print(json.dumps(value, indent=2))
            else:
                print(value)
        else:
            print(f"Secret '{args.name}' not found in {args.backend} backend", file=sys.stderr)
            sys.exit(1)
    elif args.action == "set":
        if not args.value:
            print("Error: --value is required for 'set' action", file=sys.stderr)
            sys.exit(1)
        
        success = manager.set_secret(args.name, args.value, args.backend)
        if success:
            print(f"Secret '{args.name}' successfully stored in {args.backend} backend")
        else:
            print(f"Failed to store secret '{args.name}' in {args.backend} backend", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
```

## Usage Examples

1. **Store a secret in the system keyring**:
   ```bash
   python secrets_manager.py set "myapp:api_key" --value "your_api_key_here" --backend keyring
   ```

2. **Retrieve a secret from the system keyring**:
   ```bash
   python secrets_manager.py get "myapp:api_key" --backend keyring
   ```

3. **Store a secret in AWS Secrets Manager**:
   ```bash
   python secrets_manager.py set "myapp/api_key" --value '{"key": "your_api_key_here"}' --backend aws
   ```

4. **Retrieve a secret from AWS Secrets Manager**:
   ```bash
   python secrets_manager.py get "myapp/api_key" --backend aws
   ```

5. **Store a secret as an environment variable**:
   ```bash
   python secrets_manager.py set "API_KEY" --value "your_api_key_here" --backend env
   ```

6. **Retrieve a secret from environment variables**:
   ```bash
   python secrets_manager.py get "API_KEY" --backend env
   ```

When you're finished managing secrets, ensure that sensitive information is properly secured and not left in plaintext files or terminal history.