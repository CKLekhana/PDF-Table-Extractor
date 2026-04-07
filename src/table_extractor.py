import camelot

def extract_tables(page):
    tables = page.find_tables()
    
    results = []
    i = 0
    for t in tables:
        data = t.extract()
        results.append({
            "bbox": t.bbox,
            "data": data
        })
        print(f"table {i} : \n \t{data} \n")
        i = i + 1
        
    visualize_extraction(page, tables)
    
    return results


def extract_tables_camelot(pdf_path, page_number):

    tables = camelot.read_pdf(
        pdf_path,
        pages=str(page_number),
        flavor="lattice"
    )

    results = []

    for table in tables:
        df = table.df

        # Convert dataframe to list
        data = df.values.tolist() if not df.empty else []

        # Extract headers safely
        headers = data[0] if data else []

        results.append({
            "data": data,
            "headers": headers,
            "accuracy": table.parsing_report.get("accuracy"),
            "whitespace": table.parsing_report.get("whitespace"),
            "bbox": None  # Camelot limitation
        })
        

    return results

def visualize_extraction(page, results, margin=100):
    """
    page: The pdfplumber page object
    results: The list of dicts from your extract_tables function
    """
    # Using 'with' ensures the temp files are released immediately after saving
    with page.to_image(resolution=150) as img:
        for t in results:
            # Use dictionary access [] since your extract_tables returns a dict
            bbox = t["bbox"]
            x0, top, x1, bottom = bbox
            
            # 2. Draw the Table Bounding Box (Red)
            img.draw_rect(bbox, stroke="red", stroke_width=3)
            
            # 3. Draw the Context/Margin Areas (Blue)
            # Above margin area
            above_rect = (0, max(0, top - margin), page.width, top)
            img.draw_rect(above_rect, stroke="blue", stroke_width=1)
            
            # Below margin area
            below_rect = (0, bottom, page.width, min(page.height, bottom + margin))
            img.draw_rect(below_rect, stroke="blue", stroke_width=1)
            
        # 4. Save the result
        import os
        os.makedirs("data/output", exist_ok=True) # Ensure directory exists
        img.save("data/output/debug_tables.png")
    
    # After the 'with' block, the file is no longer "in use" by Python.