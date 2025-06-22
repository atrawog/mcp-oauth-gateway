# Reference Documentation

Complete reference for commands, configuration, and troubleshooting.

```{toctree}
:maxdepth: 2
:caption: Reference Sections

command-reference
configuration-reference
environment-variables
error-codes
troubleshooting-guide
faq
```

## Quick References

### Essential Commands
```bash
just setup          # Initial project setup
just up-fresh        # Start services with fresh build
just test            # Run test suite
just check-health    # Verify service health
just docs-build      # Build documentation
```

### OAuth Management
```bash
just oauth-show-all           # Show all OAuth data
just oauth-backup             # Backup OAuth data
just oauth-purge-expired      # Clean expired tokens
just generate-github-token    # Generate OAuth tokens
```

### Service Management
```bash
just rebuild <service>   # Rebuild specific service
just logs-follow         # Follow service logs
just check-ssl          # Check SSL certificates
```

## Reference Sections

### [Command Reference](command-reference.md)
Complete documentation of all `just` commands available in the project, organized by category with usage examples and best practices.

### Configuration Reference
Environment variables, Docker configuration, and service settings.

### Environment Variables  
Complete list of all environment variables used across services.

### Error Codes
Standard error codes returned by OAuth endpoints and MCP services.

### Troubleshooting Guide
Common issues, debugging steps, and resolution procedures.

### FAQ
Frequently asked questions about setup, configuration, and usage.