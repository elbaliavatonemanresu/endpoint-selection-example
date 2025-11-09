"""PDF Builder using PyMuPDF (fitz) for generating CTTI scenario reports."""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from src.ui.theme.tokens_loader import TokensLoader


class PDFBuilder:
    """PDF builder for creating CTTI scenario reports."""

    # Page settings
    PAGE_WIDTH = 595  # A4 width in points (8.27 inches)
    PAGE_HEIGHT = 842  # A4 height in points (11.69 inches)

    # Margins
    MARGIN_LEFT = 50
    MARGIN_RIGHT = 50
    MARGIN_TOP = 50
    MARGIN_BOTTOM = 50

    # Content area
    CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    CONTENT_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

    # Font sizes
    FONT_SIZE_TITLE = 24
    FONT_SIZE_HEADING = 18
    FONT_SIZE_SUBHEADING = 14
    FONT_SIZE_BODY = 11
    FONT_SIZE_SMALL = 9

    # Line spacing
    LINE_SPACING = 1.2

    def __init__(self):
        """Initialize PDF builder."""
        self.doc = fitz.open()  # Create new PDF
        self.current_page = None
        self.current_y = 0
        self.page_number = 0

        # Load CTTI colors
        tokens = TokensLoader.load()
        self.colors = {
            "primary": self._hex_to_rgb(tokens.color.primary),
            "secondary": self._hex_to_rgb(tokens.color.secondary),
            "accent": self._hex_to_rgb(tokens.color.accent),
            "error": self._hex_to_rgb(tokens.color.error),
            "text": self._hex_to_rgb(tokens.color.text.primary),
            "border": self._hex_to_rgb(tokens.color.border),
        }

    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """
        Convert hex color to RGB tuple (0-1 range for PyMuPDF).

        Args:
            hex_color: Hex color string (e.g., "#246BB0")

        Returns:
            Tuple of (r, g, b) in 0-1 range
        """
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return (r, g, b)

    def add_page(self) -> fitz.Page:
        """
        Add a new page to the document.

        Returns:
            The newly created page
        """
        page = self.doc.new_page(width=self.PAGE_WIDTH, height=self.PAGE_HEIGHT)
        self.current_page = page
        self.current_y = self.MARGIN_TOP
        self.page_number += 1
        return page

    def add_text(
        self,
        text: str,
        x: Optional[float] = None,
        y: Optional[float] = None,
        font_size: int = FONT_SIZE_BODY,
        color: Optional[Tuple[float, float, float]] = None,
        bold: bool = False,
        align: str = "left",
    ) -> float:
        """
        Add text to the current page.

        Args:
            text: Text to add
            x: X position (defaults to left margin)
            y: Y position (defaults to current_y)
            font_size: Font size in points
            color: RGB tuple (0-1 range), defaults to text color
            bold: Whether to use bold font
            align: Text alignment ("left", "center", "right")

        Returns:
            New Y position after text
        """
        if self.current_page is None:
            self.add_page()

        if x is None:
            x = self.MARGIN_LEFT

        if y is None:
            y = self.current_y

        if color is None:
            color = self.colors["text"]

        # Select font
        fontname = "Helvetica-Bold" if bold else "Helvetica"

        # Calculate text width for alignment
        text_width = fitz.get_text_length(text, fontname=fontname.lower(), fontsize=font_size)

        if align == "center":
            x = self.MARGIN_LEFT + (self.CONTENT_WIDTH - text_width) / 2
        elif align == "right":
            x = self.PAGE_WIDTH - self.MARGIN_RIGHT - text_width

        # Insert text
        point = fitz.Point(x, y)
        self.current_page.insert_text(
            point, text, fontname=fontname, fontsize=font_size, color=color
        )

        # Update current Y position
        new_y = y + font_size * self.LINE_SPACING
        self.current_y = new_y

        return new_y

    def add_title(self, text: str, color: Optional[Tuple[float, float, float]] = None):
        """
        Add a title (large, bold, centered).

        Args:
            text: Title text
            color: RGB tuple, defaults to primary color
        """
        if color is None:
            color = self.colors["primary"]

        self.add_text(
            text, font_size=self.FONT_SIZE_TITLE, color=color, bold=True, align="center"
        )
        self.current_y += 10  # Extra spacing after title

    def add_heading(self, text: str, color: Optional[Tuple[float, float, float]] = None):
        """
        Add a heading (medium, bold).

        Args:
            text: Heading text
            color: RGB tuple, defaults to primary color
        """
        if color is None:
            color = self.colors["primary"]

        self.add_text(text, font_size=self.FONT_SIZE_HEADING, color=color, bold=True)
        self.current_y += 5  # Extra spacing after heading

    def add_subheading(self, text: str, color: Optional[Tuple[float, float, float]] = None):
        """
        Add a subheading (smaller, bold).

        Args:
            text: Subheading text
            color: RGB tuple, defaults to secondary color
        """
        if color is None:
            color = self.colors["secondary"]

        self.add_text(text, font_size=self.FONT_SIZE_SUBHEADING, color=color, bold=True)
        self.current_y += 3

    def add_body_text(self, text: str):
        """
        Add body text (normal size).

        Args:
            text: Body text
        """
        self.add_text(text, font_size=self.FONT_SIZE_BODY)

    def add_small_text(self, text: str):
        """
        Add small text (caption/footer size).

        Args:
            text: Small text
        """
        self.add_text(text, font_size=self.FONT_SIZE_SMALL)

    def add_horizontal_line(self, y: Optional[float] = None, color: Optional[Tuple[float, float, float]] = None):
        """
        Add a horizontal line across the page.

        Args:
            y: Y position (defaults to current_y)
            color: RGB tuple, defaults to border color
        """
        if self.current_page is None:
            self.add_page()

        if y is None:
            y = self.current_y

        if color is None:
            color = self.colors["border"]

        # Draw line
        start = fitz.Point(self.MARGIN_LEFT, y)
        end = fitz.Point(self.PAGE_WIDTH - self.MARGIN_RIGHT, y)
        self.current_page.draw_line(start, end, color=color, width=1)

        self.current_y = y + 10

    def add_spacing(self, points: int = 10):
        """
        Add vertical spacing.

        Args:
            points: Number of points to add
        """
        self.current_y += points

    def add_table(
        self, headers: list, rows: list, col_widths: Optional[list] = None
    ):
        """
        Add a simple table to the page.

        Args:
            headers: List of header strings
            rows: List of row data (each row is a list)
            col_widths: Optional list of column widths (must sum to CONTENT_WIDTH)
        """
        if self.current_page is None:
            self.add_page()

        num_cols = len(headers)
        if col_widths is None:
            # Equal width columns
            col_widths = [self.CONTENT_WIDTH / num_cols] * num_cols

        # Draw header row
        x = self.MARGIN_LEFT
        header_y = self.current_y

        # Header background
        header_rect = fitz.Rect(
            self.MARGIN_LEFT,
            header_y,
            self.PAGE_WIDTH - self.MARGIN_RIGHT,
            header_y + 20,
        )
        self.current_page.draw_rect(header_rect, color=self.colors["accent"], fill=self.colors["accent"])

        # Header text
        for i, header in enumerate(headers):
            self.add_text(
                header,
                x=x + 5,
                y=header_y + 15,
                font_size=self.FONT_SIZE_BODY,
                bold=True,
                color=self.colors["primary"],
            )
            x += col_widths[i]

        self.current_y = header_y + 25

        # Draw data rows
        for row in rows:
            x = self.MARGIN_LEFT
            row_y = self.current_y

            # Check if we need a new page
            if row_y + 20 > self.PAGE_HEIGHT - self.MARGIN_BOTTOM:
                self.add_page()
                row_y = self.current_y

            for i, cell in enumerate(row):
                self.add_text(
                    str(cell), x=x + 5, y=row_y + 15, font_size=self.FONT_SIZE_BODY
                )
                x += col_widths[i]

            # Row border
            self.add_horizontal_line(y=row_y + 20, color=self.colors["border"])

    def save(self, output_path: str):
        """
        Save the PDF to a file.

        Args:
            output_path: Path where to save the PDF
        """
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save document
        self.doc.save(output_path)
        self.doc.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        try:
            if self.doc is not None and not self.doc.is_closed:
                self.doc.close()
        except Exception as e:
            # Document already closed or invalid - log but don't raise during cleanup
            import sys
            print(f"Warning: Error closing PDF document: {e}", file=sys.stderr)
