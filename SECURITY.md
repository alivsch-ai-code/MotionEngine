# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public issue
2. Email the maintainers with a description of the vulnerability
3. Include steps to reproduce if possible
4. Allow reasonable time for a fix before public disclosure

We will acknowledge receipt within 48 hours and provide an estimated timeline for a fix.

## Scope

vdsim is a simulation tool intended for offline research and development. It does not handle authentication, network services (except the optional local API server), or sensitive user data. Security concerns are most relevant to:

- The optional REST API server (`vdsim.api.server`)
- File parsing (trajectory loaders, scenario JSON, OpenDRIVE XML)
- Plugin loading (custom nodes)
