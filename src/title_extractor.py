import re


# ---------- Helpers ----------

def is_text_heavy(cell):
    if not cell:
        return False
    text = str(cell)
    num_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    return num_ratio < 0.3  # mostly text


def clean_lines(lines):
    cleaned = []
    for line in lines:
        line = line.strip()

        if not line:
            continue

        if len(line) < 5:
            continue

        # skip numeric-heavy lines
        num_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
        if num_ratio > 0.4:
            continue

        cleaned.append(line)

    return cleaned


# ---------- Step 1: Find text-heavy column ----------

def find_text_column(table_data):
    if not table_data:
        return 0

    num_cols = max(len(row) for row in table_data if row)

    scores = [0] * num_cols

    for row in table_data[:5]:  # only top rows
        for i in range(len(row)):
            if is_text_heavy(row[i]):
                scores[i] += 1

    # pick column with highest text score
    return scores.index(max(scores)) if scores else 0


# ---------- Step 2: Extract candidates from that column ----------

def extract_column_candidates(table_data):
    col_idx = find_text_column(table_data)

    lines = []

    for row in table_data[:5]:
        if len(row) > col_idx and row[col_idx]:
            parts = str(row[col_idx]).split("\n")
            lines.extend(parts)

    return clean_lines(lines)


# ---------- Step 3: Extract from context (fallback) ----------

def extract_context_candidates(context_text):
    if not context_text:
        return []

    lines = context_text.split("\n")
    lines = [l.strip() for l in lines if l.strip()]

    return clean_lines(lines[-5:])  # last few lines above table


# ---------- Step 4: Pick best candidate ----------

def pick_best(lines):
    if not lines:
        return None

    # choose longest meaningful line
    return max(lines, key=len)

#----- Step 5: Score the candidates
def score_title_candidate(line):
    score = 0
    line = line.strip()

    if not line:
        return -1

    # length (titles are longer)
    if len(line) > 15:
        score += 2

    # penalize very short (headers)
    if len(line.split()) <= 3:
        score -= 2

    # date presence → strong title signal
    if re.search(r"\d{2}[./-]\d{2}[./-]\d{2,4}", line):
        score += 3

    # numeric-heavy → likely data/header
    num_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
    if num_ratio > 0.3:
        score -= 2

    # contains multiple words → good
    if len(line.split()) > 4:
        score += 2

    return score


# ---------- Final API ----------

def extract_title(context_text, table_data):

    candidates = []

    # --- from column ---
    col_candidates = extract_column_candidates(table_data)
    candidates.extend(col_candidates)

    # --- from context ---
    context_candidates = extract_context_candidates(context_text)
    candidates.extend(context_candidates)

    if not candidates:
        # fallback → header stitch
        if table_data:
            return " ".join([str(c) for c in table_data[0] if c])
        return "Untitled Table"

    # --- score all ---
    best_line = None
    best_score = -999

    for line in candidates:
        s = score_title_candidate(line)

        if s > best_score:
            best_score = s
            best_line = line

    return best_line


'''
# the heuristics and the logic was poor to get any kind of good results
import re

KEYWORDS = [
    "account", "statement", "summary", "report",
    "balance", "income", "capital", "period", "ended"
]


def classify_row(row):
    if not row:
        return "unknown"

    cells = [str(c).strip() for c in row if c and str(c).strip()]
    num_cells = len(cells)

    if num_cells == 0:
        return "unknown"

    joined = " ".join(cells).lower()

    # numeric ratio
    num_chars = sum(c.isdigit() for c in joined)
    ratio = num_chars / max(len(joined), 1)

    # --- DATA ---
    if ratio > 0.4:
        return "data"

    # --- TITLE (fake header) ---
    if num_cells == 1:
        if len(joined) > 20:
            return "title"
        if any(k in joined for k in KEYWORDS):
            return "title"

    # --- REAL HEADER ---
    if num_cells >= 2:
        short_words = all(len(c.split()) <= 3 for c in cells)
        if short_words:
            return "header"

    return "unknown"


def extract_title_and_header(table_data):
    title_candidates = []
    header = None

    for row in table_data[:5]:
        row_type = classify_row(row)

        if row_type == "title":
            title_candidates.append(" ".join([str(c) for c in row if c]))

        elif row_type == "header" and header is None:
            header = [str(c) for c in row]

    # pick best title
    title = None
    if title_candidates:
        title = max(title_candidates, key=len)

    return title, header


def extract_title(context_text, table_data):
    # 🔥 Step 1: structured extraction
    title, header = extract_title_and_header(table_data)

    if title:
        return title

    # 🔹 fallback: context
    if context_text:
        lines = [l.strip() for l in context_text.split("\n") if l.strip()]
        if lines:
            return lines[-1]

    return "Untitled Table"
'''

'''
#this uses ollama but is of no good use. introduces noisy information or oversees explicit title candidates

import re
import ollama


def clean_text(text):
    """Basic cleanup to remove noise."""
    if not text:
        return ""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines[-5:])  # keep last few lines (closest to table)


def format_table_snippet(table_data, max_rows=3):
    """Convert table rows to readable text."""
    if not table_data:
        return ""

    snippet_rows = table_data[:max_rows]
    return "\n".join(
        [" | ".join([str(cell).strip() for cell in row if cell]) for row in snippet_rows]
    )


def regex_title_extraction(text):
    """Try extracting explicit titles."""
    if not text:
        return None

    # Common patterns
    patterns = [
        r"(Table\s*\d+[:.\-]?\s*.*)",                      # Table 1: ...
        r"([A-Z][A-Z\s]{10,})",                            # ALL CAPS titles
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){2,})"              # Title Case phrases
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    return None


def slm_generate_title(context_text, table_snippet):
    """Use Ollama SLM to infer title."""
    
    prompt = f"""
        You are an expert document analyzer.

        Your task is to identify or generate a concise title for a table.

        Rules:
        - Ignore metadata (Name, Year, Assessment Year, etc.)
        - Prefer meaningful headings describing the table
        - Titles may be uppercase or multi-line — combine if needed
        - If no title exists, generate a short 3-5 word title from the table
        - Remove words like "continued"
        - Find the sentence that most resembles a title and output only that sentence
        - Output ONLY the title

        Context:
        {context_text}

        Table:
        {table_snippet}
    """

    try:
        result = ollama.generate(
            model="mistral:7b-instruct",  # use your installed model
            prompt=prompt,
            options={
                "n_predict": 20,
                "temperature": 0.2  # more deterministic
            }
        )

        if result and "response" in result:
            title = result["response"].strip()

            # Basic cleanup
            title = re.sub(r'^(title:|table:)', '', title, flags=re.I).strip()
            title = title.replace("\n", " ")

            return title if title else None

    except Exception as e:
        print(f"SLM fallback failed: {e}")

    return None


def extract_title(context_text, table_data):
    """
    Hybrid title extraction:
    1. Regex (fast)
    2. SLM fallback (robust)
    3. Header fallback (last resort)
    """

    # --- Step 1: Clean context ---
    context_text = clean_text(context_text)

    # --- Step 2: Regex extraction ---
    title = regex_title_extraction(context_text)
    if title:
        return title

    # --- Step 3: Prepare SLM inputs ---
    table_snippet = format_table_snippet(table_data)

    # --- Step 4: SLM fallback ---
    title = slm_generate_title(context_text, table_snippet)
    if title:
        return title

    # --- Step 5: Final fallback (headers) ---
    if table_data and len(table_data) > 0:
        headers = table_data[0]
        return " | ".join([str(h) for h in headers[:3]])

    return "Untitled Table"
'''

'''
# this approach used a brute force ruled based method
# it failed when metadata or other relevant information that 
# is not part of the data was included within the header cells of the table

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
'''