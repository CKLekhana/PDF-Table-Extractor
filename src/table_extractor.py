import camelot
from src.header_extractor import extract_true_header

# For OCR
import easyocr
from pdf2image import convert_from_path
import numpy as np

def extract_tables_camelot(pdf_path, page_number):
    tables = camelot.read_pdf(pdf_path, pages=str(page_number), flavor="lattice")
    if not tables:
        # fallback: stream flavor
        tables = camelot.read_pdf(pdf_path, pages=str(page_number), flavor="stream")
        
    results = []

    for table in tables:
        df = table.df
        all_data = df.values.tolist() if not df.empty else []

        # Extract header and its index
        headers, header_idx = extract_true_header(all_data)

        # Fix headers with \n inside cells
        #if headers:
        #    new_headers = []
        #    for h in headers:
        #        new_headers.extend(str(h).split("\n"))
        #    headers = [c.strip() for c in new_headers if c.strip()]

        # Data rows below header
        data = all_data[header_idx + 1:] if header_idx != -1 else all_data
        print(headers)
        results.append({
            "data": all_data,
            "headers": headers,
            "first_row": data[0] if data else [],
            "last_row": data[-1] if data else [],
            "confidence": table.parsing_report.get("accuracy"),
            "source": "camelot"
        })

    return results


# Initialize EasyOCR once
reader = easyocr.Reader(['en'])

def extract_text_from_scanned_page(pdf_path, page_num):
    """
    OCR a single scanned PDF page and return text.
    """
    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
    img = images[0]
    img_np = np.array(img)
    text_list = reader.readtext(img_np, detail=0)
    return " ".join(text_list)