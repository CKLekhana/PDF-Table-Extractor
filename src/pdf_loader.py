import pdfplumber


def normalize_text(text):
    return " ".join(text.split())


def load_pdf(pdf_path):
    pages_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):

            width = page.width
            height = page.height

            # Extract words (best starting point)
            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=2,
                keep_blank_chars=False,
                use_text_flow=True
            )

            word_blocks = []
            for w in words:
                text = normalize_text(w["text"])
                if text:
                    word_blocks.append({
                        "text": text,
                        "bbox": [w["x0"], w["top"], w["x1"], w["bottom"]]
                    })

            # Extract lines (grouped words)
            lines = []
            current_line = []
            current_top = None

            for w in word_blocks:
                if current_top is None:
                    current_top = w["bbox"][1]

                # group words into same line (y proximity)
                if abs(w["bbox"][1] - current_top) < 3:
                    current_line.append(w)
                else:
                    if current_line:
                        lines.append(merge_words_to_line(current_line))
                    current_line = [w]
                    current_top = w["bbox"][1]

            if current_line:
                lines.append(merge_words_to_line(current_line))

            pages_data.append({
                "page_index": page_index,
                "width": width,
                "height": height,
                "words": word_blocks,
                "lines": lines,
                "image": None  # optional: fill if needed later
            })

    return pages_data


def merge_words_to_line(words):
    text = " ".join([w["text"] for w in words])
    x0 = min(w["bbox"][0] for w in words)
    y0 = min(w["bbox"][1] for w in words)
    x1 = max(w["bbox"][2] for w in words)
    y1 = max(w["bbox"][3] for w in words)

    return {
        "text": text,
        "bbox": [x0, y0, x1, y1]
    }