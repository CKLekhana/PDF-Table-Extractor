# PDF Table Title & Page Number Extractor

## Objective
This project extracts tables from PDF documents and identifies their titles along with page numbers.

Develop a Python-based solution to:
- Detect tables in financial statement PDFs
- Extract table titles
- Extract corresponding page numbers
- Output results in structured format (JSON)

## Problem Scope

The solution is designed to:

- Process PDF files (digital and scanned-like)
- Detect tables using layout-based approaches
- Extract titles using contextual text near tables
- Generate structured output with:
  - `Table Title`
  - `Page Number`
- Handle edge cases:
  - Multi-page tables
  - Missing titles



## High-Level Design
![alt text](<Pipeline Design.png>)


## Implementation Details

### 1. PDF Processing
- Extracts page-wise text and layout information
- Uses structured text lines with bounding boxes



### 2. Table Detection

**Primary:**
- Camelot (for structured PDFs)

**Fallback:**
- YOLOv8-based table detection (for complex layouts)



### 3. Text-to-Table Mapping

- Extracts candidate lines:
  - Above the table
  - Inside the table (metadata/ header rows)
- Filters and cleans candidate text



### 4. Header & Footer Extraction

- Extracts top and bottom regions of the page
- Used for page number detection



### 5. Multi-Page Table Handling

- Pre-merge based on:
  - Page continuity
  - Column similarity
  - Layout alignment

- Post-merge based on:
  - Title similarity
  - Adjacent pages



### 6. Title & Page Number Extraction

- Uses LLM (via Ollama) to:
  - Select best title from candidates
  - Extract page number from header/footer

- Includes:
  - Deterministic prompting
  - JSON-enforced outputs
  - Fallback logic



### 7. Output Formatting

Example output:

```json
[
  {
    "title": "Consolidated Balance Sheet",
    "page_start": 12,
    "page_end": 13,
    "num_pages": 2,
    "table accuracy": 92.5
  }
]
```


## How to Run

### 1. Clone this project
```bash
git clone https://github.com/CKLekhana/PDF-Table-Extractor
cd PDF-Table-Extractor
```

### 2. Install Dependencies and activate environment
```bash
pip install -r requirements.txt
cd .venv/Scripts/activate.bat
```

### 3. Table Title and Page number extraction logic uses local Ollama model 


#### Install Ollama

Download and install Ollama from:
https://ollama.com


#### Pull Required Model

```bash
ollama pull llama3.2:3b
```

### 4. Run the pipeline
```bash 
python -m src.main --input <input_pdf_path> --output <output_json_path>
```

### Example
```bash 
python -m src.main --input Data/input/Document1.pdf --output Data/output/Document1.json
```


## Results & Performance Analysis

### Dataset Overview
Total documents tested: 6
Includes:
- Standard financial tables
- Multi-page tables
- Stylised layouts
- Digitised (scanned-like) PDFs



### Overall Performance
- Successfully processed: 4 / 6 documents
- Failure cases: 2 / 6 documents

### Failure Cases
#### Case 1: Stylised Multi-Column Layouts
Heavily formatted documents with two-column structures
Issues:
- Table boundaries unclear
- Text alignment inconsistent
Impact:
- Table detection fails or becomes unreliable
#### Case 2: Digitised (Scanned-like) PDFs
Visually resemble scanned documents but contain text layer
Issues:
- Irregular spacing
- Weak structural consistency
Impact:
- Reduced table detection accuracy
### Multi-Page Table Merging Performance
Overall merging accuracy: ~70–80% (excluding failure cases)
Observations:
- Fully correct merging: 1 case
- Partial merging (~90%): 1 case
- Expected: 8 tables merged
- Achieved: 6 tables merged
### Title Extraction Performance
Successful for all 4 working documents
Handles:
- Titles above tables
- Titles inside tables
- Missing titles
Special Case:
In one document, No title was present.
System generated a contextually appropriate title

### Page Number Extraction
- Extracted from:
  - Header/Footer text
- Fallback:
  - Page index used when detection fails

## Key Strengths
- Hybrid table detection (Camelot + YOLO)
- Context-aware title extraction (llama 3.2 3B)
- Robust candidate filtering
- Multi-page table handling
- Graceful fallback mechanisms

## Limitations
Performance drops for:
- Stylised layouts
- Digitised/scanned-like PDFs
- Merging depends on detection accuracy
- Limited dataset size (6 documents)

## Future Improvements
- Fine-tune SOTA layout detection models
- Introduce document-type-aware pipelines (scanned vs digital)
- Hybrid CV + NLP page number extraction
- Expand dataset for better generalisation
- Improve LLM prompting with more diverse samples


## Conclusion

This project demonstrates a hybrid approach combining:

- Rule-based methods
- Computer vision
- Language models

to solve table title and page number extraction in financial PDFs.

While effective on standard documents, further improvements are required for highly stylised and scanned-like PDFs.

## LICENSE
This project is licensed under the Apache License 2.0.

See the `LICENSE` file for more details.