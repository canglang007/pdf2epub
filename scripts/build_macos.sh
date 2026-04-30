#!/usr/bin/env bash
# Build macOS .app bundle with PyInstaller
set -euo pipefail

cd "$(dirname "$0")/.."

# Ensure dependencies are installed
pip install -e .

# Clean previous build
rm -rf build dist *.spec

# Build GUI .app (onedir + windowed = double-clickable .app)
pyinstaller --onedir \
    --windowed \
    --name "pdf2epub" \
    --exclude PyQt5 \
    --exclude PySide6 \
    --exclude matplotlib \
    --hidden-import "customtkinter" \
    --hidden-import "PIL._tkinter_finder" \
    --collect-submodules "pdf2epub" \
    src/pdf2epub/gui.py

echo "macOS build complete: dist/pdf2epub.app"
