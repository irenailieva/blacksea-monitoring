import sys

try:
    import docx
except ImportError:
    print("python-docx not installed yet")
    sys.exit(1)

def extract_docx(path, out_path):
    doc = docx.Document(path)
    text = []
    for p in doc.paragraphs:
        text.append(p.text)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text))
    print(f"Extracted to {out_path}")

if __name__ == "__main__":
    extract_docx(r"C:\Users\irena\Downloads\GLAVA_4.docx", "docx_content.txt")
