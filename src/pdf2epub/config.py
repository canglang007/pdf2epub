"""Application configuration."""

APP_NAME = "pdf2epub"
APP_VERSION = "0.2.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# EPUB generation defaults
EPUB_DEFAULT_LANGUAGE = "zh-CN"
EPUB_DEFAULT_AUTHOR = "Unknown"

# Output file extension
OUTPUT_EXTENSION = ".epub"

# Supported input file extensions
SUPPORTED_INPUT_EXTENSIONS = [
    ("PDF Files", "*.pdf"),
    ("All Files", "*.*"),
]
