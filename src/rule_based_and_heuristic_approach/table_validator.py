def is_valid_table(table, strict=False):
    data = table.get("data", [])

    if not data or len(data) < 2:
        return False

    num_cols = max(len(row) for row in data if row)

    if num_cols < 2:
        return False

    total = sum(len(row) for row in data)
    filled = sum(1 for row in data for c in row if str(c).strip())

    if total == 0:
        return False

    fill_ratio = filled / total

    if strict:
        if fill_ratio < 0.5:
            return False
    else:
        if fill_ratio < 0.3:
            return False

    text = " ".join(str(c) for row in data for c in row)
    digit_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)

    if strict:
        if digit_ratio < 0.1:
            return False
    else:
        if digit_ratio < 0.05:
            return False

    return True