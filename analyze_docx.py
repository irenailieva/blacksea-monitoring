import docx
import json

def analyze_doc(path):
    doc = docx.Document(path)
    sections = []
    current_section = {"title": "Start", "paragraphs": [], "code_blocks": []}
    
    in_code_block = False
    current_code = []
    
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if not text:
            continue
            
        # Very rough heuristic for a section title (e.g., "1.", "2.1.", or all caps)
        if text[0].isdigit() and "." in text[:5] and len(text) < 100:
            if current_section["paragraphs"] or current_section["code_blocks"]:
                sections.append(current_section)
            current_section = {"title": text, "paragraphs": [], "code_blocks": []}
            continue
            
        # Code block heuristic: starts with "# ", "def ", "import ", "SELECT ", "ALTER ", "export ", "class ", "interface "
        # Or if it has indentation
        is_code = False
        if text.startswith(("# ", "def ", "import ", "SELECT ", "ALTER ", "export ", "class ", "interface ", "import {", "const ", "let ", "<", "ST_")):
            is_code = True
            
        if is_code:
            current_code.append(text)
        else:
            if current_code:
                current_section["code_blocks"].append({"lines": current_code})
                current_code = []
            current_section["paragraphs"].append(text)
            
    if current_code:
         current_section["code_blocks"].append({"lines": current_code})
    sections.append(current_section)
    
    # Summary
    summary = []
    for s in sections:
        summary.append({
            "title": s["title"],
            "code_block_count": len(s["code_blocks"]),
            "avg_code_lines": sum(len(c["lines"]) for c in s["code_blocks"]) / max(1, len(s["code_blocks"]))
        })
        
    with open("doc_analysis.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    analyze_doc(r"C:\Users\irena\Downloads\GLAVA_4.docx")
