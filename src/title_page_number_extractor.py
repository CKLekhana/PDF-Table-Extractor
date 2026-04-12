import json
import ollama
import re
import math

def extract_title_and_page_llm(candidate_texts, header_text, footer_text, page_index):

    if not candidate_texts:
        candidate_texts = ["Unknown Title"]

    formatted_candidates = "\n".join([f"- {c}" for c in candidate_texts])

    #print(header_text)
    #print(footer_text)
    
    
    prompt = f"""
                You are an expert in financial document analysis.

                Your task is to extract:
                1. The most appropriate table title
                2. The correct page number

                INPUT:

                Candidate lines:
                {formatted_candidates}

                Header text:
                {header_text}

                Footer text:
                {footer_text}

                INSTRUCTIONS:

                TITLE SELECTION:

                - Choose ONLY ONE line from the candidate lines as the table title

                - A valid table title:
                - is descriptive and complete (usually a phrase or sentence)
                - often contains financial terms (e.g., Balance Sheet, Statement, Report)
                - appears above the table OR sometimes inside the table before column headers

                - A valid title usually has:
                - more than 3 words
                - natural language structure (not just keywords)

                STRICTLY REJECT candidates that look like column headers:
                - lines with short phrases separated by spaces or symbols
                - lines containing repeated financial terms like:
                "Assets Liabilities Equity"
                "Revenue Expenses Profit"
                - lines where most words are single tokens or labels
                - lines that look like categories rather than a sentence

                STRICTLY IGNORE:
                - numeric-heavy lines
                - column headers
                - names of people, organizations, or addresses
                - header/footer content
                - lines containing IDs, codes, or financial account numbers

                VERY IMPORTANT:
                - Column headers are NOT titles
                - NEVER return column headers as title

                PAGE NUMBER EXTRACTION:

                - Extract a valid integer ONLY from header or footer
                - Do NOT infer or generate numbers
                - Ignore years, dates, and section numbers

                OUTPUT RULES:
                - If no valid title → "Unknown Title"
                - If no valid page number → {page_index + 1}
                - Output ONLY valid JSON (no extra text)

                OUTPUT FORMAT:
                {{
                "title": "string",
                "page_number": integer
                }}
            """

    try:
        response = ollama.chat(
                model="llama3.2:3b",
                messages=[{"role": "user", "content": prompt}],
                format= 'json',
                options={
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "top_k": 1,
                    "repeat_penalty": 1.0,
                    "seed": 42
                }
            )

        content = response["message"]["content"]
        #print(content)
        result = safe_json_parse(content)

        if result is None:
            raise ValueError("Invalid JSON")

        title = result.get("title", "Unknown Title")
        page_number = result.get("page_number", page_index + 1)
        
        #print(content)
        
        #print(page_number, page_index)
        try:
            page_number = int(page_number)
        except:
            page_number = page_index + 1

        
#        print(response)

        return {
            "title": title,
            "page_number": page_number, 
        }

    except Exception as e:
        print("LLM parsing error:", e)

        return {
            "title": fallback_title(candidate_texts),
            "page_number": page_index + 1
        }
        
        
# -- helper functions

def fallback_title(candidates):
    if not candidates:
        return "Unknown Title"

    scored = [(c, score_title_candidate(c)) for c in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[0][0]        
        
def score_title_candidate(line):
    score = 0
    line = line.strip()

    if not line:
        return -1

    # length (titles are longer)
    if len(line) > 15:
        score += 2

    # penalize very short (headers)
    if len(line.split()) <= 3:
        score -= 2

    # date presence → strong title signal
    if re.search(r"\d{2}[./-]\d{2}[./-]\d{2,4}", line):
        score += 3

    # numeric-heavy → likely data/header
    num_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
    if num_ratio > 0.3:
        score -= 2

    # contains multiple words → good
    if len(line.split()) > 4:
        score += 2

    # ---------- NEW: uppercase bonus ----------
    # all uppercase
    if line.isupper():
        score += 3

    # title case (each word starts uppercase)
    elif all(w[0].isupper() for w in line.split() if w):
        score += 2

    return score

def safe_json_parse(content):
    try:
        return json.loads(content)
    except:
        # Try extracting JSON substring
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
    return None

