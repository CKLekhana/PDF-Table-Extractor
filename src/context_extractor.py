def extract_context(page, bbox, margin=100):
    x0, top, x1, bottom = bbox

    above = page.crop((x0, max(0, top - margin), x1, top)).extract_text()
    below = page.crop((x0, bottom, x1, bottom + margin)).extract_text()

    return above, below