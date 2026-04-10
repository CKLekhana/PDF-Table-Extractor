from difflib import SequenceMatcher
from src.map_text_to_tables import match_lines_to_table


# ---------- Similarity Helpers ----------

def normalize_text_list(lst):
    return " ".join([str(x).strip().lower() for x in lst if x])


def header_similarity(h1, h2):
    t1 = normalize_text_list(h1)
    t2 = normalize_text_list(h2)
    if not t1 or not t2:
        return 0
    return SequenceMatcher(None, t1, t2).ratio()


def x_overlap(b1, b2):
    x0_1, _, x1_1, _ = b1
    x0_2, _, x1_2, _ = b2

    overlap = min(x1_1, x1_2) - max(x0_1, x0_2)
    width = max(x1_1 - x0_1, x1_2 - x0_2)

    return overlap / max(width, 1)


def is_vertical_continuation(prev, curr):
    """
    True multi-page tables:
    - previous table ends near bottom
    - next table starts near top
    """
    prev_h = prev.get("page_height", 1000)
    curr_h = curr.get("page_height", 1000)

    prev_bottom = prev["bbox"][3]
    curr_top = curr["bbox"][1]

    prev_near_bottom = prev_bottom > 0.75 * prev_h
    curr_near_top = curr_top < 0.25 * curr_h

    return prev_near_bottom and curr_near_top


# ---------- Core Merge Logic ----------

def is_continuation(prev, curr):

    # 1. Must be consecutive pages
    if curr["page_index"] != prev["page_index"] + 1:
        return False

    # 2. Column count must match
    if prev["n_cols"] != curr["n_cols"]:
        return False

    # 3. Header similarity (tight)
    if header_similarity(prev["header"], curr["header"]) < 0.75:
        return False

    # 4. Horizontal alignment
    if x_overlap(prev["bbox"], curr["bbox"]) < 0.7:
        return False

    # 5. Width similarity
    w1 = prev["bbox"][2] - prev["bbox"][0]
    w2 = curr["bbox"][2] - curr["bbox"][0]

    if abs(w1 - w2) / max(w1, 1) > 0.15:
        return False

    # 🔥 6. Vertical continuity (MOST IMPORTANT)
    if not is_vertical_continuation(prev, curr):
        return False

    return True


# ---------- Merge Tables ----------

def merge_multipage_tables(tables):
    if not tables:
        return []

    tables = sorted(tables, key=lambda x: x["page_index"])

    merged = []
    i = 0

    while i < len(tables):
        group = [tables[i]]
        j = i + 1

        while j < len(tables) and is_continuation(group[-1], tables[j]):
            group.append(tables[j])
            j += 1

        merged.append({
            "tables": group
        })

        i = j

    return merged


# ---------- Candidate Collection ----------

def collect_group_candidates(group, pages, page_header_footer):
    all_candidates = []
    all_headers = []
    all_footers = []
    accuracies = []

    for table in group["tables"]:
        page_index = table["page_index"]
        table_bbox = table["bbox"]
        page_data = pages[page_index]

        matched = match_lines_to_table(page_data, table_bbox)

        # Collect all nearby text
        for key in ["above", "inside", "below"]:
            all_candidates.extend([m["text"] for m in matched.get(key, [])])

        # Collect header/footer
        header_lines = page_header_footer[page_index]["header"]
        footer_lines = page_header_footer[page_index]["footer"]

        all_headers.extend([l["text"] for l in header_lines])
        all_footers.extend([l["text"] for l in footer_lines])

        # Accuracy aggregation
        acc = table.get("accuracy")
        if acc is not None:
            accuracies.append(acc)

    # Compute group accuracy
    group_accuracy = sum(accuracies) / len(accuracies) if accuracies else None

    return all_candidates, all_headers, all_footers, group_accuracy


# ---------- Deduplication ----------

def deduplicate(lines):
    seen = set()
    result = []

    for line in lines:
        line = line.strip()
        if line and line not in seen:
            seen.add(line)
            result.append(line)

    return result


# Post title and pg no extraction merging 
def title_similarity(t1, t2):
    if not t1 or not t2:
        return 0
    return SequenceMatcher(None, t1.lower(), t2.lower()).ratio()

def is_strong_title(title):
    if not title:
        return False

    title = title.lower()

    weak_words = ["table", "data", "summary"]
    
    return not any(w in title for w in weak_words) and len(title) > 10

def merge_after_llm(results):
    if not results:
        return []

    results = sorted(results, key=lambda x: x["page_start"])

    merged = []
    i = 0

    while i < len(results):
        current = results[i]
        j = i + 1

        while j < len(results):
            next_table = results[j]

            # Check adjacency
            if current["page_end"] + 1 != next_table["page_start"]:
                break

            # Check title strength
            if not (is_strong_title(current["title"]) and is_strong_title(next_table["title"])):
                break

            # Check title similarity
            if title_similarity(current["title"], next_table["title"]) < 0.85:
                break

            # ✅ Merge
            current["page_end"] = next_table["page_end"]

            # Keep better title (longer)
            if len(next_table["title"]) > len(current["title"]):
                current["title"] = next_table["title"]

            # Merge confidence if exists
            if "confidence" in current and "confidence" in next_table:
                current["confidence"] = (current["confidence"] + next_table["confidence"]) / 2

            j += 1

        merged.append(current)
        i = j

    return merged