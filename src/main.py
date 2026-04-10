import json
import argparse
from pdf2image import convert_from_path

from src.pdf_loader import load_pdf
from src.table_extractor import extract_tables
from src.map_text_to_tables import match_lines_to_table
from src.page_header_footer_detector import extract_header_footer
from src.title_page_number_extractor import extract_title_and_page_llm
from src.table_merger import merge_multipage_tables, collect_group_candidates, deduplicate, merge_after_llm

def process_pdf(input_path, output_path):
    
    # Step 1 : Extract text from the page 
    pages = load_pdf(input_path)
    
    ''' 
    for page in pages:
        print(page.get("page_index"))
        print(page.get("lines"))
        print('-------------------------------')
    '''

    # Step 2 : Extract tables from the page
    tables = extract_tables(input_path, pages)
    
    # Step 3 : Extract header footer
    page_header_footer = {}

    for page in pages:
        page_index = page["page_index"]

        header, footer = extract_header_footer(page)

        page_header_footer[page_index] = {
            "header": header,
            "footer": footer
        }
        
    
    results = []

    merged_tables = merge_multipage_tables(tables)

    for group in merged_tables:

        first_page = group["tables"][0]["page_index"]
        last_page = group["tables"][-1]["page_index"]

        candidates, headers, footers, group_accuracy = collect_group_candidates(
            group, pages, page_header_footer
        )

        candidates = clean_candidates(deduplicate(candidates))
        headers = deduplicate(headers)
        footers = deduplicate(footers)

        if not candidates:
            candidates = ["Unknown Title"]

        header_text = " ".join(headers)
        footer_text = " ".join(footers)

        title_page_number = extract_title_and_page_llm(
            candidates,
            header_text,
            footer_text,
            first_page
        )

        llm_page = title_page_number["page_number"]

        results.append({
            "title": title_page_number["title"],
            "page_start": llm_page if llm_page else first_page,
            "page_end": last_page,
            "table accuracy": group_accuracy,
            "num_pages": len(group["tables"])
        })


    # 🔥 Post-LLM merge
    #results = merge_after_llm(results)
    
     
    for res in results:
        print("-------------------------")
        print(res)
        print("-------------------------")
        
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[DONE] Saved results to {output_path}")
    
# --- helper function
def lines_to_text(lines):
    return " ".join([l["text"] for l in lines])

def clean_candidates(candidates):
    cleaned = []

    for c in candidates:
        c = c.strip()

        if not c:
            continue

        if len(c) < 2:
            continue

        cleaned.append(c)

    return cleaned    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract table titles from PDF")
    parser.add_argument("--input", required=True, help="Path to input PDF")
    parser.add_argument("--output", default="data/output/output.json", help="Output JSON path")
    args = parser.parse_args()

    process_pdf(args.input, args.output)

