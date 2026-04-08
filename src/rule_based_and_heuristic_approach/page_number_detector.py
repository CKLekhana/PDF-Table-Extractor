import re
from difflib import SequenceMatcher

def extract_number_from_text(text):
    """Extract first integer from text"""
    matches = re.findall(r'\d+', text)
    return int(matches[0]) if matches else None

def fuzzy_page_number(text):
    """
    Try multiple strategies to detect page number:
    - Look for lines with 'page', 'pg', 'p.' etc.
    - Look at first line, last line for numbers
    """
    if not text:
        return None

    text = text.lower()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 1️⃣ Look for keywords
    for line in lines:
        if any(k in line for k in ["page", "pg", "p."]):
            num = extract_number_from_text(line)
            if num is not None:
                return num

    # 2️⃣ First line fallback
    if lines:
        num = extract_number_from_text(lines[0])
        if num is not None:
            return num

    # 3️⃣ Last line fallback
    if len(lines) > 1:
        num = extract_number_from_text(lines[-1])
        if num is not None:
            return num

    return None

def assign_page_numbers(tables):
    """
    Assign page_number field to each table.
    tables: list of table dicts with a 'context' key (text from page)
    """
    for table in tables:
        if "page_number" not in table:
            table_text = table.get("context") or ""
            table["page_number"] = fuzzy_page_number(table_text) or table.get("page_start")
    return tables