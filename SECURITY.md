# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of virtualization-mcp seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:
- **Email:** sandra@sandraschi.dev
- **Subject:** [SECURITY] Virtualization-MCP Security Issue

### What to Include

Please include the following information:
- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

- **Initial Response:** Within 48 hours
- **Status Update:** Within 7 days
- **Fix Timeline:** Critical vulnerabilities within 30 days

## Security Measures

### Current Implementation

1. **Input Validation:** All tool parameters are validated
2. **Sandboxing:** VM operations are isolated
3. **Access Control:** Path traversal protection
4. **Dependency Scanning:** Automated with Dependabot
5. **Code Scanning:** Bandit, Safety, and Semgrep in CI/CD

### Security Best Practices

When using virtualization-mcp:
- Keep VirtualBox updated to the latest version
- Use strong VM passwords
- Limit network exposure of VMs
- Regular security audits of VM configurations
- Monitor VM resource usage
- Keep the MCP server updated

## Security Scanning

We use automated security scanning:
- **Bandit:** Python security linting
- **Safety:** Dependency vulnerability scanning  
- **Semgrep:** Static analysis security testing
- **Dependabot:** Automated dependency updates

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find any similar problems
3. Prepare fixes for all supported versions
4. Release new versions as soon as possible

## Credits

We appreciate security researchers who responsibly disclose vulnerabilities. With your permission, we will publicly acknowledge your contribution.
