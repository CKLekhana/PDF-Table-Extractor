import json
from src.pdf_loader import load_pdf
from src.table_extractor import extract_tables
from src.context_extractor import extract_context
from src.title_extractor import extract_title


def process_pdf(input_path, output_path):
    pdf = load_pdf(input_path)

    results = []

    for i, page in enumerate(pdf.pages):
        tables = extract_tables(page)

        for table in tables:
            above, below = extract_context(page, table["bbox"])
            
            title = extract_title(above, table["data"])

            results.append({
                "title": title,
                "page": i + 1
            })

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved results to {output_path}")


if __name__ == "__main__":
    process_pdf("data/input/sample.pdf", "data/output/output.json")