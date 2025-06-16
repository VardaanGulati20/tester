

import re
from fpdf import FPDF

def sanitize_text(text: str) -> str:
    """Remove non-ASCII characters from the text."""
    return re.sub(r'[^\x00-\x7F]+', '', text)

def save_to_pdf(content: str, filename="output.pdf"):
    """Save the sanitized content to a PDF file."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    lines = content.split("\n")
    for line in lines:
        # Break long lines into smaller chunks to fit the PDF width
        for chunk in wrap_text(line, width=90):
            pdf.multi_cell(0, 10, chunk)

    pdf.output(filename)
    print(f"[✅] PDF saved: {filename}")

def wrap_text(text, width):
    """Wrap text manually (used for long lines)."""
    import textwrap
    return textwrap.wrap(text, width=width)
