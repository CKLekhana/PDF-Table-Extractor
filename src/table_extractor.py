import camelot
import numpy as np
from ultralytics import YOLO
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import os

def extract_tables(input_path, pages_data):
    tables = extract_tables_camelot(input_path, pages_data)

    if len(tables) == 0:
        tables = extract_tables_yolov8(input_path, pages_data)

    return tables

def extract_tables_camelot(input_path, pages_data):
    
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
        
    return results



def camelot_bbox_to_pdfplumber(bbox, page_height):
    x1, y1, x2, y2 = bbox

    return [
        x1,                 # x0
        page_height - y2,   # top
        x2,                 # x1
        page_height - y1    # bottom
    ]
    


def extract_tables_yolov8(input_path, pages_data):

    model = YOLO("https://huggingface.co/keremberke/yolov8m-table-extraction/resolve/main/best.pt")

    model.overrides['conf'] = 0.25
    model.overrides['iou'] = 0.45
    model.overrides['agnostic_nms'] = False
    model.overrides['max_det'] = 1000

    tables = []

    images = convert_from_path(input_path)

    for page_index, image in enumerate(images):

        # ✅ YOLO works fine with PIL directly
        results = model(image)

        pdf_width = pages_data[page_index]["width"]
        pdf_height = pages_data[page_index]["height"]

        # ✅ Use PIL size (cleaner than numpy)
        img_width, img_height = image.size

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])

                # 🔥 Optional: filter low confidence
                if conf < 0.3:
                    continue

                bbox = scale_bbox_to_pdf(
                    (x1, y1, x2, y2),
                    img_width,
                    img_height,
                    pdf_width,
                    pdf_height
                )

                if not is_valid_table_bbox(bbox):
                    continue

                tables.append({
                    "page_index": page_index,
                    "bbox": bbox,
                    "header": [],
                    "n_cols": 0,
                    "accuracy": conf,
                    "source": "yolov8"
                })
                
        image.close()

    del images
    
    
    
    return tables

def scale_bbox_to_pdf(bbox, img_width, img_height, pdf_width, pdf_height):

    x1, y1, x2, y2 = bbox

    scale_x = pdf_width / img_width
    scale_y = pdf_height / img_height

    return [
        x1 * scale_x,
        y1 * scale_y,
        x2 * scale_x,
        y2 * scale_y
    ]


def is_valid_table_bbox(bbox):
    x1, y1, x2, y2 = bbox

    width = x2 - x1
    height = y2 - y1

    # 🔥 tune if needed
    if width < 80 or height < 80:
        return False

    return True