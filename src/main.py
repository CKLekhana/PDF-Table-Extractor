import json
import argparse

from src.pdf_loader import load_pdf
from src.table_extractor import extract_tables_camelot
from src.context_extractor import extract_context_with_hints
from src.title_extractor import extract_title
from src.table_merger import merge_tables_across_pages
#from src.title_extractor import extract_title_and_header
from src.header_extractor import extract_true_header


def process_pdf(input_path, output_path):
    pdf = load_pdf(input_path)

    results = []

    for i, page in enumerate(pdf.pages):
        page_num = i + 1

        print(f"[INFO] Processing page {page_num}")

        # ✅ Correct Camelot usage
        tables = extract_tables_camelot(input_path, page_num)

        print(f"[INFO] Found {len(tables)} tables")

        for table in tables:
            page_text = page.extract_text() or ""
            combined_context = page_text[:1000]
            #print("Table page text : " + combined_context)
            
            title = extract_title(combined_context, table["data"])

            # fallback title if needed
            if not title:
                page_text = page.extract_text() or ""
                title = page_text[:1000].split("\n")[-1]

            # choose best header
            #headers = detected_header if detected_header else table.get("headers", [])

            #headers = table.get("headers", [])
            
            headers = extract_true_header(table['data'])

            results.append({
                "title": title,
                "page_start": page_num,
                "page_end": page_num,
                "headers": headers,
                "confidence": table.get("accuracy"),
                "source": "camelot"
            })
            
            
    # 🔥 NEW STEP: merge tables
    results = merge_tables_across_pages(results)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved results to {output_path}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract table titles from PDF")

    parser.add_argument("--input", required=True, help="Path to input PDF")
    parser.add_argument("--output", default="data/output/output.json", help="Output JSON path")

    args = parser.parse_args()

    process_pdf(args.input, args.output)

'''
#This version used pdfplumber for extracting tables
import json
from src.pdf_loader import load_pdf
from src.table_extractor import extract_tables, extract_tables_camelot
from src.context_extractor import extract_context, extract_context_with_hints
from src.title_extractor import extract_title
import argparse


def process_pdf(input_path, output_path):
    pdf = load_pdf(input_path)

    results = []

    for i, page in enumerate(pdf.pages):
        tables = extract_tables_camelot(page, i+1)

        for table in tables:
            above, below = extract_context_with_hints(page, table["bbox"])
            
            combined_context = f"{above}\n{below}"
            title = extract_title(combined_context, table["data"])

            results.append({
                "title": title,
                "page": i + 1
            })

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved results to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract table titles from PDF")

    parser.add_argument("--input", required=True, help="Path to input PDF")
    parser.add_argument("--output", default="data/output/output.json", help="Output JSON path")

    args = parser.parse_args()

    process_pdf(args.input, args.output)
'''