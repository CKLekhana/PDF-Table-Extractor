def extract_header_footer(page_data, header_ratio=0.1, footer_ratio=0.1):
    """
    Extract header and footer lines based on vertical position.

    Args:
        page_data: dict with 'lines', 'height'
        header_ratio: top % of page
        footer_ratio: bottom % of page

    Returns:
        header_lines, footer_lines
    """

    height = page_data["height"]
    header_cutoff = height * header_ratio
    footer_cutoff = height * (1 - footer_ratio)

    header_lines = []
    footer_lines = []

    for line in page_data["lines"]:
        top = line["bbox"][1]
        bottom = line["bbox"][3]

        # Header (top of page)
        if bottom <= header_cutoff:
            header_lines.append(line)

        # Footer (bottom of page)
        elif top >= footer_cutoff:
            footer_lines.append(line)

    return header_lines, footer_lines