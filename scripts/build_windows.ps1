# Build Windows .exe with PyInstaller
# Run this on Windows, or cross-build with a CI runner

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $MyInvocation.MyCommand.Path -Parent) + "\.."

# Ensure dependencies are installed
pip install -e .

# Build GUI executable
pyinstaller --onefile `
    --windowed `
    --name "pdf2epub" `
    --add-data "src/pdf2epub:pdf2epub" `
    --hidden-import "customtkinter" `
    --hidden-import "PIL._tkinter_finder" `
    --collect-submodules "pdf2epub" `
    src/pdf2epub/gui.py

Write-Host "Windows build complete: dist/pdf2epub.exe"
