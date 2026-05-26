import docx
import re

doc = docx.Document(r'C:\Users\irena\Downloads\GLAVA_4.docx')
for p in doc.paragraphs:
    if not p.text.strip():
        continue
    old = p.text
    new = re.sub(r'\bжизненоважни\b', 'важни', old, flags=re.IGNORECASE)
    new = re.sub(r'\bкритичните\b', 'основните', new, flags=re.IGNORECASE)
    new = re.sub(r'\bизключителната\b', 'голямата', new, flags=re.IGNORECASE)
    if new != old:
        style = p.style
        p.text = new
        p.style = style
doc.save(r'C:\Users\irena\Downloads\GLAVA_4.docx')
print("Done")
