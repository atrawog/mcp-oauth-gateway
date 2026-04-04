#!/bin/bash
# Build script for MCP OAuth Gateway JupyterBook documentation

echo "🔨 Building MCP OAuth Gateway Documentation..."
echo "============================================"

# Ensure we're in the docs directory
cd "$(dirname "$0")"

# Check if jupyter-book is available
if ! command -v jupyter-book &> /dev/null; then
    echo "❌ jupyter-book not found. Installing via uv..."
    cd ..
    uv sync
    cd docs
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf _build/

# Build the book
echo "📚 Building JupyterBook..."
jupyter-book build .

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Documentation built successfully!"
    echo ""
    echo "📖 View the documentation:"
    echo "   Local: file://$(pwd)/_build/html/index.html"
    echo "   Serve: python -m http.server -d _build/html 8080"
    echo ""
else
    echo ""
    echo "❌ Build failed! Check the errors above."
    exit 1
fi
