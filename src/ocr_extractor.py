import easyocr
from pdf2image import convert_from_path
import numpy as np
from src.header_extractor import extract_true_header
# Initialize EasyOCR once
reader = easyocr.Reader(['en'])

def extract_text_from_scanned_page(pdf_path, page_num):
    """
    Extract text from a single page of a scanned PDF using EasyOCR.
    
    Args:
        pdf_path (str): Path to the PDF file
        page_num (int): 1-indexed page number to process

    Returns:
        str: The extracted text for the page
    """
    # Convert only the requested page to an image
    images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)
    img = images[0]  # Only one page

    print(f"[OCR] Processing page {page_num}")

    # Convert PIL image to numpy array
    img_np = np.array(img)

    # Run OCR
    text_list = reader.readtext(img_np, detail=0)
    full_text = " ".join(text_list)

    return full_text

def extract_tables_from_ocr_page(img):
    text_list = reader.readtext(np.array(img), detail=0)
    lines = "\n".join(text_list).split("\n")
    table_rows = []
    for line in lines:
        row = [c.strip() for c in re.split(r"\s{2,}", line) if c.strip()]
        if len(row) > 1:
            table_rows.append(row)

    if not table_rows:
        return []

    headers, header_idx = extract_true_header(table_rows)
    data = table_rows[header_idx + 1:] if header_idx != -1 else table_rows

    return [{
        "data": data,
        "headers": headers,
        "first_row": data[0] if data else [],
        "last_row": data[-1] if data else [],
        "confidence": 0,
        "source": "ocr"
    }]



'''
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import numpy as np

# Initialize OCR once (important for performance)
ocr = PaddleOCR(use_angle_cls=True, lang='en')


def extract_text_from_scanned(pdf_path):
    """
    Extract text from scanned PDF using PaddleOCR.

    Returns:
        List of dicts:
        [
            {
                "page": int,
                "text": str
            }
        ]
    """

    # Convert PDF → images
    images = convert_from_path(pdf_path)

    results = []

    for i, img in enumerate(images):
        print(f"[OCR] Processing page {i+1}")

        # Convert PIL image → numpy array
        img_np = np.array(img)

        # Run OCR
        ocr_result = ocr.predict(img_np)

        page_text = []

        if ocr_result and len(ocr_result) > 0:
            for line in ocr_result[0]:
                text = line[1][0]
                if text:
                    page_text.append(text)

        full_text = " ".join(page_text)

        results.append({
            "page": i + 1,
            "text": full_text
        })

    return results
    
'''