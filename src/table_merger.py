from difflib import SequenceMatcher

# ---------- Similarity Helpers ----------

def normalize_row(row):
    return [str(c).strip().lower() for c in row]

def row_similarity(r1, r2):
    r1_text = " ".join(normalize_row(r1)) if r1 else ""
    r2_text = " ".join(normalize_row(r2)) if r2 else ""
    return SequenceMatcher(None, r1_text, r2_text).ratio()

def text_similarity(a, b):
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def header_similarity(h1, h2):
    h1_text = " ".join(normalize_row(h1))
    h2_text = " ".join(normalize_row(h2))
    return text_similarity(h1_text, h2_text)

# ---------- Merge Scoring ----------

def compute_merge_score(t1, t2):
    score = 0

    # --- 1. Page continuity (mandatory) ---
    # Use page_number if available, fallback to page_start/page_end
    p1 = t1.get("page_number") or t1.get("page_end")
    p2 = t2.get("page_number") or t2.get("page_start")
    if p2 == p1 + 1:
        score += 3
    else:
        return 0  # cannot merge if not consecutive

    # --- 2. Header similarity ---
    h_sim = header_similarity(t1.get("headers", []), t2.get("headers", []))
    if h_sim > 0.80:
        score += 3
    elif h_sim > 0.60:
        score += 2

    # --- 3. Column count match ---
    if len(t1.get("headers", [])) == len(t2.get("headers", [])):
        score += 1

    # --- 4. Row continuity ---
    r_sim = row_similarity(t1.get("last_row"), t2.get("first_row"))
    if r_sim > 0.85:
        score += 4
    elif r_sim > 0.6:
        score += 2

    # --- 5. Title similarity (low weight) ---
    t_sim = text_similarity(t1.get("title"), t2.get("title"))
    if t_sim > 0.9:
        score += 1

    return score

def should_merge(t1, t2):
    return compute_merge_score(t1, t2) >= 5  # threshold can be tuned

# ---------- Merge Function ----------

def merge_tables_across_pages(tables):
    if not tables:
        return []

    # Sort by page_number if available, else page_start
    tables = sorted(tables, key=lambda x: x.get("page_number") or x.get("page_start"))

    merged = []
    current = tables[0]

    for next_table in tables[1:]:
        if should_merge(current, next_table):
            # Merge page range
            current["page_end"] = next_table.get("page_end") or next_table.get("page_number")

            # Choose best title (longer, or could score both titles later)
            if len(next_table.get("title", "")) > len(current.get("title", "")):
                current["title"] = next_table.get("title", "")

            # Average confidence
            c1 = current.get("confidence") or 0
            c2 = next_table.get("confidence") or 0
            current["confidence"] = (c1 + c2) / 2

            # Merge first/last row
            current["first_row"] = current.get("first_row") or next_table.get("first_row")
            current["last_row"] = next_table.get("last_row") or current.get("last_row")
        else:
            merged.append(current)
            current = next_table

    merged.append(current)
    return merged




'''
# this is the logic before adding page number assignment fucntion
from difflib import SequenceMatcher

# ---------- Similarity Helpers ----------

def normalize_row(row):
    """Convert all cells to lowercase strings and strip spaces"""
    return [str(c).strip().lower() for c in row]

def row_similarity(r1, r2):
    """Compute similarity between two rows"""
    r1_text = " ".join(normalize_row(r1)) if r1 else ""
    r2_text = " ".join(normalize_row(r2)) if r2 else ""
    return SequenceMatcher(None, r1_text, r2_text).ratio()

def text_similarity(a, b):
    """Compute similarity between two strings"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def header_similarity(h1, h2):
    """Compute similarity between headers"""
    h1_text = " ".join(normalize_row(h1))
    h2_text = " ".join(normalize_row(h2))
    return text_similarity(h1_text, h2_text)

# ---------- Title Scoring Helpers ----------

def score_table_title(title):
    """Score a table title based on length, uppercase, numeric content, and word count"""
    if not title:
        return -1
    score = 0
    title = title.strip()

    if len(title) > 15:
        score += 2
    if len(title.split()) <= 3:
        score -= 2
    num_ratio = sum(c.isdigit() for c in title) / max(len(title), 1)
    if num_ratio > 0.3:
        score -= 2
    if len(title.split()) > 4:
        score += 2
    if title.isupper():
        score += 3
    elif all(w[0].isupper() for w in title.split() if w):
        score += 2
    return score

def choose_best_title(title1, title2):
    """Pick the best title when merging two tables"""
    if not title1 and not title2:
        return "Untitled Table"
    if not title1:
        return title2
    if not title2:
        return title1

    score1 = score_table_title(title1)
    score2 = score_table_title(title2)
    similarity = text_similarity(title1, title2)

    if similarity > 0.8:
        # Similar titles → pick higher scored one
        return title1 if score1 >= score2 else title2

    # Different titles → optionally concatenate
    return title1

# ---------- Merge Scoring ----------

def compute_merge_score(t1, t2):
    score = 0

    # 1. Page continuity (mandatory)
    if t2["page_start"] == t1["page_end"] + 1:
        score += 3
    else:
        return 0

    # 2. Header similarity
    h_sim = header_similarity(t1.get("headers", []), t2.get("headers", []))
    if h_sim > 0.80:
        score += 3
    elif h_sim > 0.60:
        score += 2

    # 3. Column count match
    if len(t1.get("headers", [])) == len(t2.get("headers", [])):
        score += 1

    # 4. Row continuity
    r_sim = row_similarity(t1.get("last_row"), t2.get("first_row"))
    if r_sim > 0.85:
        score += 4
    elif r_sim > 0.6:
        score += 2

    # 5. Title similarity (low weight)
    t_sim = text_similarity(t1.get("title"), t2.get("title"))
    if t_sim > 0.9:
        score += 1

    return score

def should_merge(t1, t2):
    """Decide whether two tables should merge"""
    return compute_merge_score(t1, t2) >= 5

# ---------- Merge Function ----------

def merge_tables_across_pages(tables):
    if not tables:
        return []

    tables = sorted(tables, key=lambda x: x["page_start"])
    merged = []
    current = tables[0]

    for next_table in tables[1:]:
        if should_merge(current, next_table):
            # Merge page range
            current["page_end"] = next_table["page_end"]

            # Merge title intelligently
            current["title"] = choose_best_title(current.get("title"), next_table.get("title"))

            # Average confidence
            c1 = current.get("confidence") or 0
            c2 = next_table.get("confidence") or 0
            current["confidence"] = (c1 + c2) / 2

            # Optionally merge data
            # current["data"].extend(next_table.get("data", []))

            # Merge first/last row
            current["first_row"] = current.get("first_row") or next_table.get("first_row")
            current["last_row"] = next_table.get("last_row") or current.get("last_row")

        else:
            merged.append(current)
            current = next_table

    merged.append(current)
    return merged
'''

'''
from difflib import SequenceMatcher

# ---------- Similarity Helpers ----------

def normalize_row(row):
    """Convert all cells to lowercase strings and strip spaces"""
    return [str(c).strip().lower() for c in row]

def row_similarity(r1, r2):
    """Compute similarity between two rows"""
    r1_text = " ".join(normalize_row(r1)) if r1 else ""
    r2_text = " ".join(normalize_row(r2)) if r2 else ""
    return SequenceMatcher(None, r1_text, r2_text).ratio()

def text_similarity(a, b):
    """Compute similarity between two strings"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def header_similarity(h1, h2):
    """Compute similarity between headers"""
    h1_text = " ".join(normalize_row(h1))
    h2_text = " ".join(normalize_row(h2))
    return text_similarity(h1_text, h2_text)

# ---------- Merge Scoring ----------

def compute_merge_score(t1, t2):
    score = 0

    # --- 1. Page continuity (mandatory) ---
    if t2["page_start"] == t1["page_end"] + 1:
        score += 3
    else:
        return 0  # cannot merge if not consecutive

    # --- 2. Header similarity ---
    h_sim = header_similarity(t1.get("headers", []), t2.get("headers", []))
    if h_sim > 0.80:
        score += 3
    elif h_sim > 0.60:
        score += 2

    # --- 3. Column count match ---
    if len(t1.get("headers", [])) == len(t2.get("headers", [])):
        score += 1

    # --- 4. Row continuity (strong signal) ---
    r_sim = row_similarity(t1.get("last_row"), t2.get("first_row"))
    if r_sim > 0.85:
        score += 4  # very strong continuation signal
    elif r_sim > 0.6:
        score += 2

    # --- 5. Title similarity (low weight) ---
    t_sim = text_similarity(t1.get("title"), t2.get("title"))
    if t_sim > 0.9:
        score += 1

    return score

def should_merge(t1, t2):
    """Decide whether two tables should merge"""
    return compute_merge_score(t1, t2) >= 5  # can tweak threshold if needed

# ---------- Merge Function ----------

def merge_tables_across_pages(tables):
    if not tables:
        return []

    # Sort tables by page
    tables = sorted(tables, key=lambda x: x["page_start"])
    merged = []
    current = tables[0]

    for next_table in tables[1:]:
        if should_merge(current, next_table):
            # Merge page range
            current["page_end"] = next_table["page_end"]

            # Better title: choose longer
            if len(next_table.get("title", "")) > len(current.get("title", "")):
                current["title"] = next_table.get("title", "")

            # Average confidence
            c1 = current.get("confidence") or 0
            c2 = next_table.get("confidence") or 0
            current["confidence"] = (c1 + c2) / 2

            # Optionally merge data (if you want combined table data)
            # current["data"].extend(next_table.get("data", []))

            # Merge first/last row
            current["first_row"] = current.get("first_row") or next_table.get("first_row")
            current["last_row"] = next_table.get("last_row") or current.get("last_row")
        else:
            merged.append(current)
            current = next_table

    merged.append(current)
    return merged
'''

'''
from difflib import SequenceMatcher

def row_similarity(r1, r2):
    from difflib import SequenceMatcher

    r1 = " ".join(map(str, r1)).lower()
    r2 = " ".join(map(str, r2)).lower()

    return SequenceMatcher(None, r1, r2).ratio()

def text_similarity(a, b):
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def header_similarity(h1, h2):
    h1 = " ".join([str(x) for x in h1]).lower()
    h2 = " ".join([str(x) for x in h2]).lower()
    return text_similarity(h1, h2)

def compute_merge_score(t1, t2):
    score = 0

    # --- 1. Page continuity (MANDATORY) ---
    if t2["page_start"] == t1["page_end"] + 1:
        score += 3
    else:
        return 0  # cannot merge if not consecutive

    # --- 2. Header similarity ---
    h_sim = header_similarity(t1["headers"], t2["headers"])
    if h_sim > 0.85:
        score += 3
    elif h_sim > 0.65:
        score += 2

    # --- 3. Column count match ---
    if len(t1["headers"]) == len(t2["headers"]):
        score += 1

    # --- 4. 🔥 Row continuity (NEW, VERY IMPORTANT) ---
    #r_sim = row_similarity(t1.get("last_row"), t2.get("first_row"))

    #if r_sim > 0.85:
    #    score += 4   # strong signal → continuation
    #elif r_sim > 0.6:
    #    score += 2

    # --- 5. (Optional) Title similarity (LOW weight) ---
    t_sim = text_similarity(t1.get("title"), t2.get("title"))

    if t_sim > 0.9:
        score += 1  # low weight

    return score


def should_merge(t1, t2):
    return compute_merge_score(t1, t2) >= 5


def merge_tables_across_pages(tables):
    if not tables:
        return []

    tables = sorted(tables, key=lambda x: x["page_start"])

    merged = []
    current = tables[0]

    for next_table in tables[1:]:
        if should_merge(current, next_table):
            current["page_end"] = next_table["page_end"]

            # Better title
            if len(next_table["title"]) > len(current["title"]):
                current["title"] = next_table["title"]

            # Average confidence
            c1 = current.get("confidence") or 0
            c2 = next_table.get("confidence") or 0
            current["confidence"] = (c1 + c2) / 2

        else:
            merged.append(current)
            current = next_table

    merged.append(current)
    return merged



def compute_merge_score(t1, t2):
    score = 0

    # Page continuity
    if t2["page_start"] == t1["page_end"] + 1:
        score += 3
    else:
        return 0

    # Header similarity
    h_sim = header_similarity(t1["headers"], t2["headers"])
    if h_sim > 0.8:
        score += 3
    elif h_sim > 0.6:
        score += 2

    # Title similarity
    t_sim = text_similarity(t1["title"], t2["title"])
    if t_sim > 0.8:
        score += 2
    
    # Column count match
    if len(t1["headers"]) == len(t2["headers"]):
        score += 1

    return score
'''