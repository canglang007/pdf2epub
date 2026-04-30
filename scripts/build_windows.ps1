# Build Windows .exe with PyInstaller
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $MyInvocation.MyCommand.Path -Parent) + "\.."

# Ensure dependencies are installed
pip install -e .

# Clean previous build
Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue

# Build GUI executable
pyinstaller --onefile `
    --windowed `
    --name "pdf2epub" `
    --exclude PyQt5 `
    --exclude PySide6 `
    --exclude matplotlib `
    --hidden-import "customtkinter" `
    --hidden-import "PIL._tkinter_finder" `
    --collect-submodules "pdf2epub" `
    src/pdf2epub/gui.py

Write-Host "Windows build complete: dist/pdf2epub.exe"
