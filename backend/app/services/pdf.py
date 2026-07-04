"""In-memory PDF generation (fpdf2) with header/footer layout ported from the
legacy MyPDF class. Uses a bundled Unicode font when available so Spanish and
Hindi text render correctly (core PDF fonts are Latin-1 only)."""
import re
from pathlib import Path

from fpdf import FPDF

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
UNICODE_FONT = FONT_DIR / "NotoSans-Regular.ttf"
DEVANAGARI_FONT = FONT_DIR / "NotoSansDevanagari-Regular.ttf"


class ItineraryPDF(FPDF):
    def __init__(self, font_family: str):
        super().__init__()
        self.font_family_name = font_family

    def header(self):
        self.set_font(self.font_family_name, "", 16)
        self.cell(0, 10, "TravelBud", 0, 1, "C")
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family_name, "", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


def _strip_markdown(text: str) -> str:
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    return text


def build_pdf(content: str, language: str = "English") -> bytes:
    pdf: ItineraryPDF
    if language == "Hindi" and DEVANAGARI_FONT.exists() and UNICODE_FONT.exists():
        pdf = ItineraryPDF("Noto")
        pdf.add_font("Noto", "", str(UNICODE_FONT))
        pdf.add_font("NotoDeva", "", str(DEVANAGARI_FONT))
        pdf.set_fallback_fonts(["NotoDeva"])
    elif UNICODE_FONT.exists():
        pdf = ItineraryPDF("Noto")
        pdf.add_font("Noto", "", str(UNICODE_FONT))
    else:
        pdf = ItineraryPDF("Helvetica")
        # Latin-1 fallback: drop characters the core font can't encode.
        content = content.encode("latin-1", "replace").decode("latin-1")

    pdf.add_page()
    pdf.set_font(pdf.font_family_name, "", 12)
    pdf.multi_cell(0, 8, _strip_markdown(content))
    return bytes(pdf.output())
