"""Desktop GUI for pdf2epub using customtkinter."""

from __future__ import annotations

import threading
from pathlib import Path

import customtkinter as ctk

from pdf2epub.config import APP_TITLE, SUPPORTED_INPUT_EXTENSIONS
from pdf2epub.core.builder import EPUBBuilder
from pdf2epub.core.parser import PDFParser


class PDF2EPUBApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("580x320")
        self.resizable(False, False)
        ctk.set_appearance_mode("System")

        self._input_path: Path | None = None
        self._output_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self):
        # Title
        title = ctk.CTkLabel(self, text=APP_TITLE, font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(20, 10))

        # Input file selection
        input_frame = ctk.CTkFrame(self)
        input_frame.pack(fill="x", padx=30, pady=6)

        self._input_label = ctk.CTkLabel(input_frame, text="Input PDF:", width=80, anchor="w")
        self._input_label.pack(side="left", padx=(10, 5))

        self._input_entry = ctk.CTkEntry(input_frame, placeholder_text="Select a PDF file...")
        self._input_entry.pack(side="left", fill="x", expand=True, padx=5)

        self._browse_btn = ctk.CTkButton(input_frame, text="Browse", width=80, command=self._browse_input)
        self._browse_btn.pack(side="right", padx=(5, 10))

        # Output file selection
        output_frame = ctk.CTkFrame(self)
        output_frame.pack(fill="x", padx=30, pady=6)

        self._output_label = ctk.CTkLabel(output_frame, text="Output EPUB:", width=80, anchor="w")
        self._output_label.pack(side="left", padx=(10, 5))

        self._output_entry = ctk.CTkEntry(output_frame, placeholder_text="Output path (auto-generated)...")
        self._output_entry.pack(side="left", fill="x", expand=True, padx=5)

        self._output_btn = ctk.CTkButton(output_frame, text="Save As...", width=80, command=self._browse_output)
        self._output_btn.pack(side="right", padx=(5, 10))

        # Progress
        self._progress = ctk.CTkProgressBar(self, mode="indeterminate")
        self._progress.pack(fill="x", padx=30, pady=(10, 5))

        # Status label
        self._status = ctk.CTkLabel(self, text="Ready", anchor="w")
        self._status.pack(fill="x", padx=30, pady=2)

        # Convert button
        self._convert_btn = ctk.CTkButton(
            self, text="Convert", font=ctk.CTkFont(size=14, weight="bold"),
            height=40, command=self._start_conversion,
        )
        self._convert_btn.pack(pady=(10, 20))

    def _browse_input(self):
        path = ctk.filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=SUPPORTED_INPUT_EXTENSIONS,
        )
        if not path:
            return
        self._input_path = Path(path)
        self._input_entry.delete(0, "end")
        self._input_entry.insert(0, str(self._input_path))
        self._auto_output()

    def _browse_output(self):
        path = ctk.filedialog.asksaveasfilename(
            title="Save EPUB as",
            defaultextension=".epub",
            filetypes=[("EPUB Files", "*.epub")],
        )
        if not path:
            return
        self._output_path = Path(path)
        self._output_entry.delete(0, "end")
        self._output_entry.insert(0, str(self._output_path))

    def _auto_output(self):
        if self._input_path is None:
            return
        default = self._input_path.with_suffix(".epub")
        self._output_path = default
        self._output_entry.delete(0, "end")
        self._output_entry.insert(0, str(default))

    def _set_ui_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._browse_btn.configure(state=state)
        self._output_btn.configure(state=state)
        self._convert_btn.configure(state=state)

    def _start_conversion(self):
        input_text = self._input_entry.get().strip()
        if input_text:
            self._input_path = Path(input_text)

        if self._input_path is None or not self._input_path.exists():
            self._status.configure(text="Error: Please select a valid PDF file.")
            return

        output_text = self._output_entry.get().strip()
        if output_text:
            self._output_path = Path(output_text)

        if self._output_path is None:
            self._auto_output()
            if self._output_path is None:
                self._status.configure(text="Error: Please specify an output path.")
                return

        self._status.configure(text="Converting...")
        self._convert_btn.configure(text="Converting...")
        self._progress.start()
        self._set_ui_enabled(False)

        thread = threading.Thread(target=self._convert, daemon=True)
        thread.start()

    def _convert(self):
        try:
            parser = PDFParser(str(self._input_path))
            try:
                doc = parser.parse()
            finally:
                parser.close()

            builder = EPUBBuilder(doc)
            builder.build(str(self._output_path))

            self.after(0, self._on_success)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_success(self):
        self._progress.stop()
        self._progress.set(1)
        self._status.configure(text=f"Done: {self._output_path}")
        self._convert_btn.configure(text="Convert")
        self._set_ui_enabled(True)

    def _on_error(self, message: str):
        self._progress.stop()
        self._progress.set(0)
        self._status.configure(text=f"Error: {message}")
        self._convert_btn.configure(text="Convert")
        self._set_ui_enabled(True)


def main():
    app = PDF2EPUBApp()
    app.mainloop()


if __name__ == "__main__":
    main()
