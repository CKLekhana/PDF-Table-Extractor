def extract_tables(page):
    tables = page.find_tables()
    
    results = []
    for t in tables:
        data = t.extract()
        results.append({
            "bbox": t.bbox,
            "data": data
        })
    
    return results