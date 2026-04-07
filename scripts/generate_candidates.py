import os
import csv
import pdfplumber
import camelot


# ---------- Helpers ----------

def is_text_heavy(cell):
    if not cell:
        return False
    text = str(cell)
    num_ratio = sum(c.isdigit() for c in text) / max(len(text), 1)
    return num_ratio < 0.3


def find_text_column(table_data):
    if not table_data:
        return 0

    num_cols = max(len(row) for row in table_data if row)
    scores = [0] * num_cols

    for row in table_data[:5]:
        for i in range(len(row)):
            if is_text_heavy(row[i]):
                scores[i] += 1

    return scores.index(max(scores)) if scores else 0


def extract_column_candidates(table_data):
    col_idx = find_text_column(table_data)

    lines = []

    for row in table_data[:5]:
        if len(row) > col_idx and row[col_idx]:
            parts = str(row[col_idx]).split("\n")
            for p in parts:
                p = p.strip()
                if p:
                    lines.append(p)

    return lines


def extract_context_candidates(page_text):
    if not page_text:
        return []

    lines = [l.strip() for l in page_text.split("\n") if l.strip()]

    # take last few lines (above table approx)
    return lines[:]


# ---------- Core Function ----------

def generate_candidates_from_pdf(pdf_path):
    all_candidates = []

    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)

        for page_num in range(1, num_pages + 1):
            print(f"[INFO] Processing page {page_num}")

            page = pdf.pages[page_num - 1]
            page_text = page.extract_text() or ""

            try:
                tables = camelot.read_pdf(
                    pdf_path,
                    pages=str(page_num),
                    flavor="lattice"
                )
            except Exception as e:
                print(f"[WARN] Camelot failed on page {page_num}: {e}")
                continue

            for table_idx, table in enumerate(tables):
                df = table.df
                table_data = df.values.tolist()

                # --- Column-based candidates ---
                col_candidates = extract_column_candidates(table_data)

                # --- Context-based candidates ---
                context_candidates = extract_context_candidates(page_text)

                # --- Store with metadata ---
                for line in col_candidates:
                    all_candidates.append({
                        "text": line,
                        "source": "column",
                        "pdf": os.path.basename(pdf_path),
                        "page": page_num,
                        "table_id": table_idx
                    })

                for line in context_candidates:
                    all_candidates.append({
                        "text": line,
                        "source": "context",
                        "pdf": os.path.basename(pdf_path),
                        "page": page_num,
                        "table_id": table_idx
                    })

    return all_candidates


# ---------- Save to CSV ----------

def save_candidates(candidates, output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["text", "label", "source", "pdf", "page", "table_id"]
        )

        writer.writeheader()

        for c in candidates:
            c["label"] = ""  # empty for manual labeling
            writer.writerow(c)


# ---------- Main ----------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate title candidates from PDFs")

    parser.add_argument("--input_dir", required=True, help="Folder with PDFs")
    parser.add_argument("--output", default="data/candidates.csv")

    args = parser.parse_args()

    all_candidates = []

    for file in os.listdir(args.input_dir):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(args.input_dir, file)

            print(f"\n[INFO] Processing file: {file}")

            candidates = generate_candidates_from_pdf(pdf_path)
            all_candidates.extend(candidates)

    save_candidates(all_candidates, args.output)

    print(f"\n✅ Saved {len(all_candidates)} candidates to {args.output}")