import re

def extract_title(text, table_data):
    if text:
        match = re.search(r"(Table\s*\d+[:.\-]?\s*.*)", text, re.I)
        if match:
            return match.group(1)

        lines = text.split("\n")
        if lines:
            return lines[-1]

    # fallback → use headers
    if table_data and len(table_data) > 0:
        headers = table_data[0]
        return " | ".join([str(h) for h in headers[:3]])

    return "Untitled Table"