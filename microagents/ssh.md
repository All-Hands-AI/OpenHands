---
name: SSH Microagent
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - ssh
  - remote server
  - remote machine
  - remote host
  - remote connection
  - secure shell
  - ssh keys
---

# SSH Microagent

This microagent provides capabilities for establishing and managing SSH connections to remote machines.

## Capabilities

- Establish SSH connections using password or key-based authentication
- Generate and manage SSH key pairs
- Configure SSH for easier connections
- Execute commands on remote machines
- Transfer files between local and remote machines
- Manage SSH configurations and known hosts
- Store and retrieve SSH keys securely using various methods (local or password managers)

## Authentication Methods

### Password Authentication

```bash
ssh username@hostname
```

When prompted, the user will need to enter their password.

### Key-Based Authentication

Generate a new SSH key pair:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/key_name -C "comment" -N ""
```

Copy the public key to the remote server:
```bash
ssh-copy-id -i ~/.ssh/key_name.pub username@hostname
```

Connect using the private key:
```bash
ssh -i ~/.ssh/key_name username@hostname
```

## SSH Configuration

Create or edit the SSH config file for easier connections:
```bash
mkdir -p ~/.ssh
cat > ~/.ssh/config << 'EOF'
Host alias
    HostName hostname_or_ip
    User username
    IdentityFile ~/.ssh/key_name
    Port 22
    ServerAliveInterval 60
EOF
chmod 600 ~/.ssh/config
```

Then connect using the alias:
```bash
ssh alias
```

## Common SSH Options

- `-p PORT`: Connect to a specific port
- `-X`: Enable X11 forwarding
- `-L local_port:remote_host:remote_port`: Set up local port forwarding
- `-R remote_port:local_host:local_port`: Set up remote port forwarding
- `-N`: Do not execute a remote command (useful for port forwarding)
- `-f`: Run in background
- `-v`: Verbose mode (add more v's for increased verbosity)

## File Transfer with SCP

Copy a file to the remote server:
```bash
scp /path/to/local/file username@hostname:/path/to/remote/directory/
```

Copy a file from the remote server:
```bash
scp username@hostname:/path/to/remote/file /path/to/local/directory/
```

Copy a directory recursively:
```bash
scp -r /path/to/local/directory username@hostname:/path/to/remote/directory/
```

## SSH Agent

Start the SSH agent:
```bash
eval "$(ssh-agent -s)"
```

Add a key to the agent:
```bash
ssh-add ~/.ssh/key_name
```

## Troubleshooting

- Check SSH service status on remote: `systemctl status sshd`
- Verify SSH port is open: `nc -zv hostname 22`
- Debug connection issues: `ssh -vvv username@hostname`
- Check permissions: SSH private keys should have 600 permissions (`chmod 600 ~/.ssh/key_name`)
- Verify known_hosts: If host key changed, remove the old entry with `ssh-keygen -R hostname`

## Secure SSH Key Management

### Local Storage with Proper Permissions

The most basic approach is to ensure proper file permissions:

```bash
# Set correct permissions for private keys
chmod 600 ~/.ssh/id_ed25519
# Set correct permissions for public keys
chmod 644 ~/.ssh/id_ed25519.pub
# Set correct permissions for SSH directory
chmod 700 ~/.ssh
```

### Using a Password Manager

Many password managers support storing SSH keys securely:
- 1Password
- LastPass
- Bitwarden
- KeePass

### Using a Secrets Manager

For more advanced key management across multiple machines, consider using a dedicated secrets manager.

For more details on secrets management, use the Secrets Management microagent:
```
secrets management
```

## Security Best Practices

- Use key-based authentication instead of passwords
- Use strong, unique keys (ED25519 or RSA with at least 4096 bits)
- Protect private keys with passphrases
- Disable root login and password authentication on servers
- Use non-standard ports for public-facing servers
- Implement fail2ban or similar for brute force protection
- Regularly update SSH server and client software
- Store SSH keys securely using a secrets manager
- Rotate SSH keys regularly, especially after team member departures