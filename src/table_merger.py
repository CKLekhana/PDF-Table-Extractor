from difflib import SequenceMatcher


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