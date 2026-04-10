import camelot
import numpy as np

def extract_tables(input_path, pages_data):
    tables = camelot.read_pdf(input_path, pages="all", flavor='lattice')
    
    results = []
    
    for table in tables:
        page_index = table.page - 1  # camelot is 1-based
        page_height = pages_data[page_index]["height"]

        bbox = camelot_bbox_to_pdfplumber(table._bbox, page_height)

        table_info = {
            "page_index": page_index,
            "bbox": bbox,
            "header": table.data[0] if table.data else [],
            "n_cols": len(table.data[0]) if table.data else 0,
            "accuracy": table.accuracy, 
            "page_height" : page_height
        }

        results.append(table_info)

        # Debug prints (optional)
        #print(f"\nPage: {table.page}")
        #print(f"BBox (converted): {bbox}")

    return results

def camelot_bbox_to_pdfplumber(bbox, page_height):
    x1, y1, x2, y2 = bbox

    return [
        x1,                 # x0
        page_height - y2,   # top
        x2,                 # x1
        page_height - y1    # bottom
    ]