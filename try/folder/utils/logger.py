
from fpdf import FPDF
import re

def sanitize_text(text):
    # Remove emojis and non-ASCII characters
    return re.sub(r'[^\x00-\x7F]+', '', text)

def save_to_pdf(sections: dict, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for title, content in sections.items():
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 0, 128)
        pdf.cell(0, 10, title, ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0, 0, 0)

        # Wrap content line-by-line
        lines = content.split('\n')
        for line in lines:
            for chunk in split_text(line, 90):
                pdf.cell(0, 10, chunk, ln=True)
        pdf.ln(5)

    pdf.output(filename)

def split_text(text, length):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current + " " + word) <= length:
            current += " " + word
        else:
            lines.append(current.strip())
            current = word
    if current:
        lines.append(current.strip())
    return lines



