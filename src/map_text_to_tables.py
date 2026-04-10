def match_lines_to_table(page_data, table_bbox, margin=80):
    """
    Matches lines on a page to a given table bounding box.

    Args:
        page_data: dict containing 'lines'
        table_bbox: [x0, top, x1, bottom]
        margin: vertical distance threshold for nearby lines

    Returns:
        dict with categorized lines:
            {
                "above": [...],
                "inside": [...],
                "below": [...]
            }
    """

    x0, table_top, x1, table_bottom = table_bbox

    matched = {
        "above": [],
        "inside": [],
        #"below": []
    }

    for line in page_data["lines"]:
        lx0, ltop, lx1, lbottom = line["bbox"]

        # Check horizontal overlap (important!)
        horizontal_overlap = not (lx1 < x0 or lx0 > x1)

        if not horizontal_overlap:
            continue

        # Distance calculations
        distance_above = table_top - lbottom
        distance_below = ltop - table_bottom

        # ABOVE TABLE
        if 0 <= distance_above <= margin:
            matched["above"].append({
                "text": line["text"],
                "bbox": line["bbox"],
                "distance": distance_above
            })

        # INSIDE TABLE
        elif ltop >= table_top and lbottom <= table_bottom:
            matched["inside"].append({
                "text": line["text"],
                "bbox": line["bbox"]
            })

        # BELOW TABLE (optional)
        #elif 0 <= distance_below <= margin:
        #    matched["below"].append({
        #        "text": line["text"],
        #        "bbox": line["bbox"],
        #        "distance": distance_below
        #    })

    # Sort for better usability
    matched["above"] = sorted(matched["above"], key=lambda x: x["distance"])
    #matched["below"] = sorted(matched["below"], key=lambda x: x["distance"])

    return matched