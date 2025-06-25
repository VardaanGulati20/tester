from fpdf import FPDF
import re
import textwrap
import unicodedata

# ---------------------------
# PDF CLASS
# ---------------------------
class StyledPDF(FPDF):
    def header(self):
        self.set_fill_color(50, 60, 100)
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Educational Assistant - MCP Tool Output", ln=True, align="C", fill=True)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')


# ---------------------------
# SANITIZER & WRAPPER
# ---------------------------
def sanitize_text(text: str) -> str:
    """Remove emojis and non-latin1 characters for PDF compatibility."""
    text = unicodedata.normalize("NFKD", text)
    return ''.join([c for c in text if ord(c) < 256])


def wrap_text(text, width):
    return textwrap.wrap(text, width=width)


# ---------------------------
# PDF GENERATOR
# ---------------------------
def save_to_pdf(content: str, filename="output.pdf", question=""):
    content = sanitize_text(content)
    question = sanitize_text(question)

    parts = content.split("Final Agent Answer:\n")
    final_answer = parts[1].split("Full Scraped Content:\n")[0].strip() if "Full Scraped Content:" in parts[1] else parts[1]
    scraped = parts[1].split("Full Scraped Content:\n")[1].strip() if "Full Scraped Content:" in parts[1] else ""

    pdf = StyledPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ---------------------------
    # User Question
    # ---------------------------
    pdf.set_fill_color(240, 240, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "User Question", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    for line in wrap_text(question, 100):
        pdf.multi_cell(0, 8, line)

    pdf.ln(5)

    # ---------------------------
    # Structured Educational Content
    # ---------------------------
    pdf.set_fill_color(235, 255, 235)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Structured Educational Content", ln=True, fill=True)
    pdf.set_font("Arial", "", 10)

    lines = scraped.split("\n")
    seen_lines = set()
    current_section = None

    for line in lines:
        line = sanitize_text(line.strip())
        if not line or line.lower() in seen_lines:
            continue
        seen_lines.add(line.lower())

        # Skip noise
        if any(x in line.lower() for x in [
            "newsletter", "top tutorials", "privacy policy", "affiliate", 
            "tos", "editorial policy", "click here", "pdf", "join our free course"
        ]):
            continue

        # Section Headings
        if re.match(r'^(\d\)|\d+\.)', line) or line.lower().endswith("tutorial") or line.endswith(":"):
            current_section = line
            pdf.ln(3)
            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(0, 102, 204)
            pdf.multi_cell(0, 8, f"{line}")
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(0, 0, 0)
            continue

        # Bullets or enumerated points
        if line.startswith("-") or re.match(r'^\d+\.', line):
            pdf.multi_cell(0, 6, f"- {line}")
        else:
            for sub in wrap_text(line, 100):
                pdf.multi_cell(0, 6, sub)
        pdf.ln(1)

    pdf.ln(5)

    # ---------------------------
    # Final Agent Answer
    # ---------------------------
    pdf.set_fill_color(220, 240, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Final Answer from Agent", ln=True, fill=True)
    pdf.set_font("Arial", "", 11)
    for line in wrap_text(final_answer, 100):
        pdf.multi_cell(0, 8, line)

    pdf.output(filename)
    print(f"[✅] PDF saved as: {filename}")

