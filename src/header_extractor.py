
def is_text(cell):
    if not cell:
        return False
    text = str(cell).strip()
    if not text:
        return False

    num_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    return num_ratio < 0.4


def score_header_row(row):
    if not row:
        return -1

    # 1️⃣ Split multi-line cells into separate pseudo-cells
    cells = []
    for c in row:
        if not c:
            continue
        parts = str(c).split("\n")
        cells.extend([p.strip() for p in parts if p.strip()])

    num_cells = len(cells)
    # print(cells)  # optional debug
    if num_cells < 2:
        return -1  # header must have multiple columns

    score = 0

    # ✅ more columns = better
    score += num_cells

    # ✅ text-heavy cells
    text_cells = sum(1 for c in cells if is_text(c))
    score += text_cells * 2

    # ✅ short phrases (typical headers)
    short_cells = sum(1 for c in cells if len(c.split()) <= 3)
    score += short_cells

    # ❌ penalize numeric-heavy cells
    numeric_cells = sum(1 for c in cells if not is_text(c))
    score -= numeric_cells * 2

    return score

'''
def score_header_row(row):
    if not row:
        return -1



    cells = [str(c).strip() for c in row if c and str(c).strip()]
    num_cells = len(cells)

    if num_cells < 2:
        return -1  # header must have multiple columns

    score = 0

    # ✅ more columns = better
    score += num_cells

    # ✅ text-heavy cells
    text_cells = sum(1 for c in cells if is_text(c))
    score += text_cells * 2

    # ✅ short phrases (typical headers)
    short_cells = sum(1 for c in cells if len(c.split()) <= 3)
    score += short_cells

    # ❌ penalize numeric-heavy rows
    num_cells_count = sum(1 for c in cells if not is_text(c))
    score -= num_cells_count * 2

    return score
'''

def extract_true_header(table_data):
    if not table_data:
        return []

    best_row = None
    best_score = -1
    best_idx = -1

    # Only inspect top rows
    for idx, row in enumerate(table_data[:5]):
        s = score_header_row(row)

        if s > best_score:
            best_score = s
            best_row = row
            best_idx = idx

    # clean header
    if best_row:
        header = [str(c).strip() for c in best_row]
        return header, best_idx

    return [], -1