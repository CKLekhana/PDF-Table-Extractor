import json
import ollama
import re

def extract_title_and_page_llm(candidate_texts, header_text, footer_text, page_index):

    if not candidate_texts:
        candidate_texts = ["Unknown Title"]

    formatted_candidates = "\n".join([f"- {c}" for c in candidate_texts])

    prompt = f"""
You are an expert in analyzing financial documents.

INPUT:

Candidate table titles:
{formatted_candidates}

Page header text:
{header_text}

Page footer text:
{footer_text}

TASKS:

1. Select the BEST table title from the candidates.
2. Extract the page number from header or footer.

RULES:
- Ignore numeric rows or column headers
- Page number must be a valid integer
- If no title → "Unknown Title"
- If no page number → {page_index}

OUTPUT (STRICT JSON):
{{
  "title": "...",
  "page_number": ...
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

        result = safe_json_parse(content)

        if result is None:
            raise ValueError("Invalid JSON")

        title = result.get("title", "Unknown Title")
        page_number = result.get("page_number", page_index)

        try:
            page_number = int(page_number)
        except:
            page_number = page_index

        return {
            "title": title,
            "page_number": page_number
        }

    except Exception as e:
        print("LLM parsing error:", e)

        return {
            "title": fallback_title(candidate_texts),
            "page_number": page_index
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