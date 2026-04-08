import json
import argparse
from pdf2image import convert_from_path

from src.pdf_loader import load_pdf, is_scanned_page
from src.table_extractor import extract_tables_camelot, extract_text_from_scanned_page
from src.ocr_extractor import extract_tables_from_ocr_page
from src.title_extractor import extract_title
from src.table_merger import merge_tables_across_pages
from src.header_extractor import extract_true_header
from src.page_number_detector import assign_page_numbers

def process_pdf(input_path, output_path):
    pdf = load_pdf(input_path)
    ocr_images = convert_from_path(input_path)  # For scanned pages
    results = []

    for i, page in enumerate(pdf.pages):
        page_num = i + 1
        print(f"[INFO] Processing page {page_num}")

        # ---------- SCANNED PAGE ----------
        if is_scanned_page(page):
            print("[INFO] SCANNED → OCR")
            tables = extract_tables_from_ocr_page(ocr_images[i])

            page_text = "\n".join([" ".join(r) for t in tables for r in t["data"]])  # fallback context
            for table in tables:
                title = extract_title(page_text, table["data"])
                if not title:
                    title = page_text[:1000].split("\n")[-1]
                
                results.append({
                    "title": title,
                    "page_start": page_num,
                    "page_end": page_num,
                    "headers": table.get("headers"),
                    "first_row": table.get("first_row"),
                    "last_row": table.get("last_row"),
                    "confidence": table.get("confidence", 0),
                    "source": "ocr", 
                    "context": []
                })

        # ---------- DIGITAL PAGE ----------
        else:
            print("[INFO] DIGITAL → Camelot")
            tables = extract_tables_camelot(input_path, page_num)
            print(f"[INFO] Found {len(tables)} tables")

            page_text = page.extract_text() or ""
            combined_context = page_text[:50]
            #print(combined_context)
            for table in tables:
                title = extract_title(combined_context, table["data"])
                if not title:
                    title = page_text[:1000].split("\n")[-1]

                results.append({
                    "title": title,
                    "page_start": page_num,
                    "page_end": page_num,
                    "headers": table.get("headers"),
                    "first_row": table["first_row"] if table.get("first_row") else [],
                    "last_row": table["last_row"] if table.get("last_row") else [],
                    "confidence": table.get("confidence"),
                    "source": "camelot", 
                    "context" : combined_context
                })

    # Assign fuzzy page numbers based on table context
    results = assign_page_numbers(results)

    # ---------- MERGE TABLES ACROSS PAGES ----------
    results = merge_tables_across_pages(results)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[DONE] Saved results to {output_path}")

'''
def process_pdf(input_path, output_path):
    pdf = load_pdf(input_path)
    results = []

    for i, page in enumerate(pdf.pages):
        page_num = i + 1
        print(f"[INFO] Processing page {page_num}")

        # Detect scanned page
        if is_scanned_page(page):
            print("[INFO] SCANNED → OCR")
            ocr_text = extract_text_from_scanned_page(input_path, page_num)
            title = extract_title(ocr_text, [])
            # fallback if title empty
            if not title:
                title = ocr_text[:1000].split("\n")[-1]

            results.append({
                "title": title,
                "page_start": page_num,
                "page_end": page_num,
                "headers": [],
                "first_row": None,
                "last_row": None,
                "confidence": 0,
                "source": "ocr"
            })

        else:
            print("[INFO] DIGITAL → Camelot")
            tables = extract_tables_camelot(input_path, page_num)
            print(f"[INFO] Found {len(tables)} tables")

            for table in tables:
                # Use page context + table for title extraction
                page_text = page.extract_text() or ""
                combined_context = page_text[:1000]
                #print(combined_context)
                title = extract_title(combined_context, table["data"])
                
                # fallback if title is empty
                if not title:
                    title = page_text[:1000].split("\n")[-1]

                #headers, _ = extract_true_header(table['data'])
                #print(headers)

                results.append({
                    "title": title,
                    "page_start": page_num,
                    "page_end": page_num,
                    "headers": table.get("headers"),
                    "first_row": table["data"][0] if table["data"] else [],
                    "last_row": table["data"][-1] if table["data"] else [],
                    "confidence": table.get("confidence"),
                    "source": "camelot"
                })

    # Merge tables across pages
    results = merge_tables_across_pages(results)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[DONE] Saved results to {output_path}")
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract table titles from PDF")
    parser.add_argument("--input", required=True, help="Path to input PDF")
    parser.add_argument("--output", default="data/output/output.json", help="Output JSON path")
    args = parser.parse_args()

    process_pdf(args.input, args.output)


'''
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
'''
'''
def process_pdf(input_path, output_path):
    pdf = load_pdf(input_path)

    results = []

    # --- OCR fallback (precompute once) ---
    ocr_pages = extract_text_from_scanned(input_path)

    for i, page in enumerate(pdf.pages):
        page_num = i + 1

        print(f"[INFO] Processing page {page_num}")

        # 🔍 detect scanned vs digital
        if is_scanned_page(page):
            print("[INFO] Detected scanned page")

            ocr_text = ocr_pages[i]["text"]

            # extract title using your existing logic
            title = extract_title(ocr_text, [])

            results.append({
                "title": title,
                "page_start": page_num,
                "page_end": page_num,
                "source": "ocr"
            })

        else:
            print("[INFO] Detected digital page")

            tables = extract_tables_camelot(input_path, page_num)

            for table in tables:
                title = extract_title("", table["data"])

                results.append({
                    "title": title,
                    "page_start": page_num,
                    "page_end": page_num,
                    "headers": table.get("headers"),
                    "first_row": table.get("first_row"),
                    "last_row": table.get("last_row"),
                    "confidence": table.get("confidence"),
                    "source": "camelot"
                })

    # 🔥 merge only camelot tables (optional improvement later)
    results = merge_tables_across_pages(results)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved results to {output_path}")
'''
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