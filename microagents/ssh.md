---
name: SSH Connection Manager
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - ssh
  - remote
  - connect
  - remote machine
  - remote server
---

# SSH Connection Manager

This microagent helps with SSH connections to remote machines, including connecting, executing commands, and properly exiting when finished.

## Capabilities

- Connect to remote machines using SSH
- Execute commands on remote machines
- Transfer files between local and remote machines
- Properly exit SSH sessions when finished

## Usage

### Connecting to a Remote Machine

```bash
# Basic SSH connection
ssh username@hostname

# SSH with specific port
ssh -p 2222 username@hostname

# SSH with identity file
ssh -i /path/to/private_key username@hostname
```

### Executing Commands on Remote Machines

```bash
# Execute a command and return
ssh username@hostname "command"

# Execute multiple commands
ssh username@hostname "command1 && command2"
```

### Transferring Files

```bash
# Copy local file to remote
scp /path/to/local/file username@hostname:/path/to/remote/directory

# Copy remote file to local
scp username@hostname:/path/to/remote/file /path/to/local/directory

# Copy directory recursively
scp -r /path/to/local/directory username@hostname:/path/to/remote/directory
```

### Exiting SSH Sessions

To properly exit an SSH session:

1. Type `exit` or `logout` at the remote shell prompt
2. Alternatively, press `Ctrl+D` to send EOF

## Error Handling

### Connection Issues

If you encounter connection issues:

1. Verify the hostname or IP address is correct
2. Ensure the SSH service is running on the remote machine
3. Check if a firewall is blocking the connection
4. Verify your credentials are correct

### Authentication Issues

If you encounter authentication issues:

1. Verify your username and password
2. Check if your SSH key is properly configured
3. Ensure your SSH key has the correct permissions (600 for private keys)

## Best Practices

1. Use SSH keys instead of passwords for better security
2. Keep your SSH client and server software updated
3. Use a non-standard port for SSH to reduce automated attacks
4. Consider using SSH config files for frequently accessed hosts
5. Always exit SSH sessions properly when finished

## Example SSH Config

```
# ~/.ssh/config
Host myserver
    HostName server.example.com
    User username
    Port 22
    IdentityFile ~/.ssh/id_rsa
```

With this config, you can simply use `ssh myserver` to connect.