---
name: Secrets Management
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - secrets management
  - manage secrets
  - store secrets
  - retrieve secrets
  - secure credentials
  - api keys
  - vault
  - keyring
  - secure storage
  - aws secrets
  - aws secretsmanager
---

# Secrets Management Microagent

This microagent provides guidance and capabilities for securely storing, retrieving, and managing secrets across different platforms and environments, with special focus on AWS Secrets Manager and SSH keys.

## Capabilities

- Store and retrieve secrets using various methods
- Implement best practices for secrets management
- Configure applications to use secrets securely
- Rotate and update secrets
- Integrate with different secret storage solutions
- Manage SSH keys securely

## Secret Storage Solutions

### 1. AWS Secrets Manager

Enterprise-grade secret management with rotation capabilities.

#### Prerequisites

- AWS CLI installed and configured with appropriate credentials
- Python with boto3 library for programmatic access

#### Configuration

Set up AWS credentials:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Or configure using AWS CLI:

```bash
aws configure
```

#### Creating and Managing Secrets

**Create a New Secret:**

```bash
aws secretsmanager create-secret \
    --name "your-secret-name" \
    --description "Description of your secret" \
    --secret-string '{"key1":"value1","key2":"value2"}'
```

**Using Python:**

```python
import boto3
import json

def create_secret(secret_name, secret_value, description=""):
    """Create a new secret in AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    
    response = client.create_secret(
        Name=secret_name,
        Description=description,
        SecretString=json.dumps(secret_value)
    )
    
    return response['ARN']
```

**Retrieve a Secret:**

```bash
aws secretsmanager get-secret-value --secret-id "your-secret-name"
```

**Using Python:**

```python
def get_secret(secret_name):
    """Retrieve a secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    
    response = client.get_secret_value(SecretId=secret_name)
    
    if 'SecretString' in response:
        return json.loads(response['SecretString'])
    else:
        # For binary secrets
        return response['SecretBinary']
```

**Update an Existing Secret:**

```bash
aws secretsmanager put-secret-value \
    --secret-id "your-secret-name" \
    --secret-string '{"key1":"new-value1","key2":"new-value2","key3":"value3"}'
```

**List All Secrets:**

```bash
aws secretsmanager list-secrets
```

**Delete a Secret:**

```bash
# With recovery window
aws secretsmanager delete-secret \
    --secret-id "your-secret-name" \
    --recovery-window-in-days 7
```

#### Organizing Secrets in AWS

Organize secrets in a structured JSON format:

```json
{
  "environment": "development",
  "api_keys": {
    "service1": "key1",
    "service2": "key2"
  },
  "database": {
    "host": "db_host",
    "username": "db_user",
    "password": "db_password"
  },
  "ssh_keys": {
    "key_name1": {
      "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n...\n-----END OPENSSH PRIVATE KEY-----",
      "public_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAID85dE8jVI9B4RiGSzBbRqifCoCQ+D+BuBcvKayA92tU key-comment"
    },
    "config": "Host example-server\n    HostName example.com\n    User admin\n    IdentityFile ~/.ssh/key_name\n    Port 22"
  }
}
```

#### Adding to Categories

```python
def add_to_category(secret_name, category, key, value):
    """Add a key-value pair to a category in a secret"""
    # Get current secret
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    secret_data = json.loads(response['SecretString'])
    
    # Create category if it doesn't exist
    if category not in secret_data:
        secret_data[category] = {}
    
    # Add or update the key-value pair
    secret_data[category][key] = value
    
    # Update the secret
    client.put_secret_value(
        SecretId=secret_name,
        SecretString=json.dumps(secret_data)
    )
```

### 2. Environment Variables

Simple but effective for local development and containerized applications.

**Setting environment variables:**

```bash
# Linux/macOS
export API_KEY="your-api-key"

# Windows (Command Prompt)
set API_KEY=your-api-key

# Windows (PowerShell)
$env:API_KEY="your-api-key"
```

**Using in applications:**

```python
# Python
import os
api_key = os.environ.get('API_KEY')
```

### 3. .env Files

Popular for development environments, using libraries like python-dotenv or dotenv.

**Creating a .env file:**

```
DATABASE_URL=postgres://user:password@localhost/dbname
API_KEY=your-api-key
DEBUG=True
```

**Using in applications:**

```python
# Python with python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.environ.get('API_KEY')
```

### 4. HashiCorp Vault

Advanced secret management with fine-grained access control.

```python
import hvac

# Initialize the client
client = hvac.Client(url='https://vault.example.com:8200')

# Authenticate
client.auth.token.login(token='my-token')

# Read a secret
secret = client.secrets.kv.v2.read_secret_version(
    path='my-secret',
    mount_point='secret'
)
```

### 5. System Keyring

Local secure storage using the operating system's credential manager.

```python
import keyring

# Store a secret
keyring.set_password("system", "username", "password")

# Retrieve a secret
password = keyring.get_password("system", "username")
```

## Managing SSH Keys

SSH keys require special handling due to their format, permissions requirements, and usage patterns.

### Generating SSH Keys

```bash
# Generate ED25519 key (modern, recommended)
ssh-keygen -t ed25519 -f ~/.ssh/key_name -C "your_email@example.com"

# Generate RSA key (traditional)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/key_name -C "your_email@example.com"
```

### Storing SSH Keys in AWS Secrets Manager

Create a Python script to store SSH keys:

```python
#!/usr/bin/env python3
import boto3
import json
import os

def read_file(file_path):
    """Read the content of a file"""
    with open(file_path, 'r') as file:
        return file.read().strip()

def update_secret_with_ssh_keys(secret_name):
    """Update AWS Secrets Manager secret with SSH keys"""
    client = boto3.client('secretsmanager')
    
    # Get the current secret value
    response = client.get_secret_value(SecretId=secret_name)
    current_secret = json.loads(response['SecretString'])
    
    # Initialize ssh_keys category if it doesn't exist
    if 'ssh_keys' not in current_secret:
        current_secret['ssh_keys'] = {}
    
    # Read SSH keys
    ssh_dir = os.path.expanduser('~/.ssh')
    
    # Example for a specific key
    key_name = "my_key"
    private_key = read_file(os.path.join(ssh_dir, key_name))
    public_key = read_file(os.path.join(ssh_dir, f"{key_name}.pub"))
    
    current_secret['ssh_keys'][key_name] = {
        'private_key': private_key,
        'public_key': public_key
    }
    
    # SSH config
    ssh_config = read_file(os.path.join(ssh_dir, 'config'))
    current_secret['ssh_keys']['config'] = ssh_config
    
    # Update the secret
    client.put_secret_value(
        SecretId=secret_name,
        SecretString=json.dumps(current_secret)
    )
    
    print(f"Successfully stored SSH keys in {secret_name}")
```

### Retrieving SSH Keys from AWS Secrets Manager

Create a Python script to retrieve SSH keys:

```python
#!/usr/bin/env python3
import boto3
import json
import os
import stat

def ensure_directory(directory):
    """Ensure a directory exists with proper permissions"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.chmod(directory, stat.S_IRWXU)  # 700 permissions (rwx------)

def write_file(file_path, content, permissions=0o600):
    """Write content to a file with specific permissions"""
    with open(file_path, 'w') as file:
        file.write(content)
    os.chmod(file_path, permissions)

def retrieve_ssh_keys(secret_name):
    """Retrieve SSH keys from AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    
    # Get the secret value
    response = client.get_secret_value(SecretId=secret_name)
    secret_data = json.loads(response['SecretString'])
    
    if 'ssh_keys' not in secret_data:
        print("No SSH keys found in the secret")
        return False
    
    ssh_keys = secret_data['ssh_keys']
    ssh_dir = os.path.expanduser('~/.ssh')
    
    # Ensure SSH directory exists with proper permissions
    ensure_directory(ssh_dir)
    
    # Process each key set
    for key_name, key_data in ssh_keys.items():
        if key_name == 'config':
            # Handle SSH config file
            config_path = os.path.join(ssh_dir, 'config')
            write_file(config_path, key_data, 0o600)
            print(f"Saved SSH config to {config_path}")
        else:
            # Handle key pairs
            if isinstance(key_data, dict) and 'private_key' in key_data and 'public_key' in key_data:
                # Save private key
                private_key_path = os.path.join(ssh_dir, key_name)
                write_file(private_key_path, key_data['private_key'], 0o600)
                print(f"Saved private key to {private_key_path}")
                
                # Save public key
                public_key_path = os.path.join(ssh_dir, f"{key_name}.pub")
                write_file(public_key_path, key_data['public_key'], 0o644)
                print(f"Saved public key to {public_key_path}")
    
    print("SSH keys retrieved and saved successfully")
    return True
```

### SSH Key Permissions

SSH requires specific file permissions:

```bash
# Set correct permissions for SSH directory
chmod 700 ~/.ssh

# Set correct permissions for private keys
chmod 600 ~/.ssh/id_ed25519

# Set correct permissions for public keys
chmod 644 ~/.ssh/id_ed25519.pub

# Set correct permissions for config file
chmod 600 ~/.ssh/config
```

## Best Practices

### General Guidelines

1. **Never hardcode secrets** in application code or commit them to version control
2. **Use different secrets** for development, testing, and production environments
3. **Implement least privilege access** to secrets
4. **Rotate secrets regularly**, especially after team member departures
5. **Audit secret access** to detect unauthorized usage
6. **Encrypt secrets at rest and in transit**
7. **Use temporary credentials** when possible
8. **Implement secret revocation** procedures

### AWS Secrets Manager Best Practices

1. Use IAM roles with least privilege for accessing secrets
2. Enable AWS CloudTrail to audit secret access
3. Use VPC endpoints to access Secrets Manager without internet exposure
4. Implement automatic secret rotation for sensitive credentials
5. Use resource-based policies to control access to specific secrets
6. Tag secrets for better organization and access control
7. Use AWS KMS customer managed keys for additional encryption control

### SSH Key Best Practices

1. Use ED25519 or RSA 4096-bit keys for strong security
2. Protect private keys with passphrases
3. Store private keys securely and never share them
4. Regularly rotate SSH keys, especially after team member departures
5. Use SSH config files to manage multiple connections
6. Consider certificate-based authentication for enterprise environments
7. Implement SSH key management solutions for teams

## Secret Rotation

### Manual Rotation Process

1. Generate a new secret value
2. Update the secret in the storage solution
3. Update applications to use the new secret
4. Verify functionality with the new secret
5. Revoke the old secret

### Automated Rotation

Many cloud providers offer automated rotation:

- AWS Secrets Manager can automatically rotate RDS credentials
- Azure Key Vault supports automatic rotation with Function Apps
- HashiCorp Vault provides dynamic secrets with automatic expiration

## Application Integration

### Example: Retrieving Database Credentials from AWS Secrets Manager

```python
import boto3
import json
import os
from botocore.exceptions import ClientError

def get_database_credentials():
    """Retrieve database credentials from Secrets Manager"""
    secret_name = os.environ.get('DB_SECRET_NAME', 'database-credentials')
    region_name = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        
        return {
            'host': secret.get('database', {}).get('host'),
            'username': secret.get('database', {}).get('username'),
            'password': secret.get('database', {}).get('password'),
            'port': secret.get('database', {}).get('port', 5432)
        }
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise e
```

### Example: Using SSH Keys from AWS Secrets Manager

```python
import boto3
import json
import os
import subprocess
import tempfile

def run_ssh_command_with_stored_key(secret_name, host, command):
    """Run SSH command using a key stored in AWS Secrets Manager"""
    # Get the key from Secrets Manager
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    secret_data = json.loads(response['SecretString'])
    
    # Get the SSH key
    ssh_keys = secret_data.get('ssh_keys', {})
    key_name = 'my_key'  # Replace with your key name
    key_data = ssh_keys.get(key_name, {})
    
    if not key_data or 'private_key' not in key_data:
        raise ValueError(f"SSH key '{key_name}' not found in secret")
    
    # Create a temporary file for the private key
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as key_file:
        key_file.write(key_data['private_key'])
        key_file_path = key_file.name
    
    try:
        # Set proper permissions for the key file
        os.chmod(key_file_path, 0o600)
        
        # Run the SSH command
        ssh_cmd = [
            'ssh',
            '-i', key_file_path,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            host,
            command
        ]
        
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"SSH command failed: {result.stderr}")
        
        return result.stdout
    finally:
        # Clean up the temporary key file
        os.unlink(key_file_path)
```

## Troubleshooting

### Common Issues

1. **Secret not found**: Verify the secret name and environment
2. **Permission denied**: Check access permissions for the current user/role
3. **Expired credentials**: Renew authentication tokens or credentials
4. **SSH key permission issues**: Ensure correct file permissions (600 for private keys)
5. **SSH connection failures**: Check network connectivity and server configuration

### Debugging Tips

- Use verbose logging temporarily (ensure secrets are redacted)
- Verify environment variables are correctly set
- Check for typos in secret names or paths
- Ensure the correct region/project is configured for cloud services
- Use `ssh -v` (or `-vv`, `-vvv`) for detailed SSH connection debugging

## Security Considerations

1. **Secure the CI/CD pipeline**: Use dedicated secret management for CI/CD
2. **Container security**: Use Kubernetes secrets or mount secrets at runtime
3. **Monitoring**: Set up alerts for unusual secret access patterns
4. **Secret sprawl**: Regularly audit and clean up unused secrets
5. **Compliance**: Ensure secret management meets regulatory requirements