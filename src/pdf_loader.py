import pdfplumber
import re

def load_pdf(path):
    return pdfplumber.open(path)

def is_scanned_page(page):
    text = page.extract_text()

    if not text:
        return True

    text = text.strip()

    # --- Heuristic 1: Too short ---
    if len(text) < 30:
        return True

    # --- Heuristic 2: Too many non-alphanumeric chars ---
    alnum_ratio = sum(c.isalnum() for c in text) / len(text)

    if alnum_ratio < 0.5:
        return True

    # --- Heuristic 3: Few valid words ---
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)

    if len(words) < 5:
        return True

    return False