# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in vboxmcp, we appreciate your help in disclosing it to us in a responsible manner.

### How to Report

Please report security vulnerabilities by emailing our security team at [security@example.com](mailto:security@example.com). You should receive a response within 48 hours. If you don't receive a response, please follow up via email to ensure we received your original message.

### What to Include

When reporting a vulnerability, please include:
- A description of the vulnerability
- Steps to reproduce the issue
- Any potential impact
- Your contact information (optional)

### Our Pledge

We will:
- Acknowledge receipt of your report within 48 hours
- Work on a fix as soon as possible
- Keep you informed about the progress
- Credit you in our security advisories (unless you prefer to remain anonymous)

### Bug Bounty

We currently do not have a formal bug bounty program, but we are happy to recognize and thank researchers who help us keep our users safe.

## Security Best Practices

### For Users
- Always run vboxmcp with the principle of least privilege
- Keep your VirtualBox installation up to date
- Regularly update vboxmcp to the latest version
- Review and understand the permissions you grant to vboxmcp

### For Developers
- Follow secure coding practices
- Keep dependencies up to date
- Use the security scanning tools provided in the CI/CD pipeline
- Review and address security alerts from GitHub's Dependabot

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.1, 1.0.2). We recommend always running the latest patch version of your installed major.minor version.

## Disclosure Policy

- When a security vulnerability is reported, we will work on a fix as soon as possible
- Once a fix is ready, we will release a new version and publish a security advisory
- We will credit the reporter unless they wish to remain anonymous
