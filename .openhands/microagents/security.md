---
name: security
type: knowledge
version: 1.0.0
agent: CodeActAgent
triggers:
  - security
  - secure
  - vulnerability
  - authentication
  - authorization
---

This microagent provides guidance on security best practices and helps identify potential security vulnerabilities in code and system design.

## Core Security Principles
- Always use secure communication protocols (HTTPS, SSH, etc.)
- Never store sensitive data (passwords, tokens, keys) in code or version control
- Apply the principle of least privilege
- Validate and sanitize all user inputs
- Keep dependencies updated and regularly check for vulnerabilities

## Common Security Checks
- Ensure proper authentication and authorization mechanisms
- Verify secure session management
- Check for proper input validation and sanitization
- Confirm secure storage of sensitive data
- Validate secure configuration of services and APIs

## Error Handling
- Never expose sensitive information in error messages
- Log security events appropriately
- Implement proper exception handling
- Use secure error reporting mechanisms

## Limitations
- Cannot perform active security scanning
- Does not replace professional security audits
- Limited to code-level and configuration security guidance