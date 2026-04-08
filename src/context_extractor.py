def extract_context(page, bbox, margin=100):
    x0, top, x1, bottom = bbox

    above = page.crop((x0, max(0, top - margin), x1, top)).extract_text()
    below = page.crop((x0, bottom, x1, bottom + margin)).extract_text()

    return above, below

def extract_context_with_hints(page, bbox, margin=100):
    x0, top, x1, bottom = bbox
    
    def process_crop(crop_area):
        if not crop_area:
            return ""
        
        # Extract words with font metadata
        words = crop_area.extract_words(extra_attrs=["fontname", "size"])
        
        processed_parts = []
        for word in words:
            # Check for Bold or larger font size (adjust '11' based on your PDF)
            is_bold = "Bold" in word.get("fontname", "")
            is_large = word.get("size", 0) > 11
            
            text = word['text']
            if is_bold or is_large:
                processed_parts.append(f"[HEADING]{text}[/HEADING]")
            else:
                processed_parts.append(text)
        
        return " ".join(processed_parts).strip()

    # --- Extract Above ---
    # We use page.width to ensure we catch titles that might be centered or offset
    above_area = page.crop((0, max(0, top - margin), page.width, top))
    context_above = process_crop(above_area)

    # --- Extract Below ---
    # Useful for footnotes or "Table continued..." markers
    below_area = page.crop((0, bottom, page.width, min(page.height, bottom + margin)))
    context_below = process_crop(below_area)
            
    return context_above, context_below