# PDF Table Title Extractor

## Overview
This project extracts tables from PDF documents and identifies their titles along with page numbers.

---

## High-Level Design

Pipeline:

1. Load PDF
2. Detect tables using pdfplumber
3. Extract context (text above table)
4. Apply heuristics to detect/generate table titles
5. Output results as JSON

---

## Implementation Details

### Libraries Used

- pdfplumber  
  → For table detection and text extraction from digital PDFs

- re (regex)  
  → For identifying table title patterns

- json  
  → Output formatting

---

## How to Run

```bash
pip install -r requirements.txt
python -m src.main
```

## License
This project is licensed under the Apache License 2.0.