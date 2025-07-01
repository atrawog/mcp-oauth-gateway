# MCP OAuth Gateway Documentation

This directory contains comprehensive JupyterBook documentation for the MCP OAuth Gateway project.

## 📚 Documentation Structure

The documentation is organized into the following sections:

- **Getting Started** - Overview and quick start guide
- **Architecture** - System design and component architecture
- **Development Tools** - Justfile reference and commands
- **Python Packages** - Documentation for all 6 Python packages
- **Service Implementations** - Details on all 15 services
- **API Reference** - Complete API documentation
- **Operations** - Deployment and monitoring guides

## 🏗️ Building the Documentation

### Using justfile (Recommended)

```bash
# From project root
just docs-build
```

### Using the build script

```bash
# From docs directory
./build.sh
```

### Manual build

```bash
# Ensure jupyter-book is installed
pixi install

# Build the documentation
jupyter-book build docs/
```

## 👀 Viewing the Documentation

### Local File Access

Open `docs/_build/html/index.html` in your browser.

### Local Web Server

```bash
# From project root
python -m http.server -d docs/_build/html 8080

# Then visit http://localhost:8080
```

### Production Deployment

The built documentation in `_build/html/` can be deployed to any static hosting service:
- GitHub Pages
- Netlify
- Vercel
- S3 + CloudFront

## 📝 Documentation Standards

All documentation follows these principles:

1. **Real Implementation Only** - Every feature documented exists in code
2. **CLAUDE.md Compliance** - Follows all sacred commandments
3. **No Mocks** - Examples use real services
4. **Complete Coverage** - All commands, packages, and services documented

## 🔧 Editing Documentation

1. Edit markdown files in the appropriate subdirectory
2. Follow the existing structure and format
3. Run `just docs-build` to verify changes
4. Commit changes to git

## 📊 Documentation Statistics

- **Total Files**: 50+ documentation files
- **Justfile Commands**: 100+ commands documented
- **Python Packages**: 6 packages fully documented
- **Services**: 15 services (13 MCP + 2 infrastructure)
- **API Endpoints**: Complete OAuth 2.1 and MCP reference

## 🚀 Key Features Documented

### Architecture
- Three-layer separation (Traefik → Auth → MCP)
- OAuth 2.1 with RFC 7591/7592
- Dual MCP patterns (proxy and native)
- Security architecture

### Development
- Complete justfile reference
- Testing patterns (no mocks!)
- Docker orchestration
- OAuth management

### Services
- Infrastructure services (Traefik, Auth, Redis)
- Proxy pattern MCP services
- Native pattern MCP services
- Health monitoring

## 🔍 Quick Links

- [Overview](overview.md)
- [Justfile Reference](justfile-reference.md)
- [Python Packages](packages/index.md)
- [Service Documentation](services/index.md)
- [API Reference](api/index.md)

## 🛟 Troubleshooting

### Build Errors

If the build fails:

1. Check all referenced files exist
2. Verify markdown syntax
3. Ensure jupyter-book is installed
4. Check for missing dependencies

### Missing Content

The documentation references all components. If something appears missing:

1. Check if the service is enabled in `.env`
2. Verify the component exists in the codebase
3. Review the _toc.yml structure

## 📖 Documentation Maintenance

Keep documentation updated:

1. Update when adding new features
2. Document new justfile commands
3. Add new services to appropriate sections
4. Maintain API documentation accuracy

---

Built with ❤️ following the sacred commandments of CLAUDE.md
