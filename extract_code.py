import docx
import json

def extract_code(path):
    doc = docx.Document(path)
    code = []
    current = []
    
    # We will identify code blocks by checking if a paragraph looks like code.
    # It's better to just extract paragraphs that have monospace font OR look like code.
    # But since docx formatting might be tricky, we'll use heuristic:
    prefixes = ('# ', '//', '/*', '*/', 'import ', 'export ', 'def ', 'class ', 'const ', 'let ', '<', 'ST_', '@', 'module.exports', 'rf =', 'xgb_model =', 'lgb_model =', 'X_train', 'prob1 =', 'avg_prob =', 'final_pred =', 'yhat =', 'return ', 'user: ', 'isLoading: ', 'error: ', '...', 'id:', 'read:', 'timestamp:', 'notifications:', 'unreadCount:', '{ name:', 'item =>', 'baseURL:', 'headers:', 'content:', 'theme:', 'plugins:', '--', 'job.status', 'size=', 'variant=', 'className=', 'const [', 'api.get', '])', 'const csv', 'const blob', 'clearInterval', 'const newRes', 'const newest', 'if (newest)', 'with rasterio.open')
    suffixes = ('{', '}', ';', '/>', '",', "',", "')")
    
    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
            
        is_code = False
        if t.startswith(prefixes) or t.endswith(suffixes):
            is_code = True
        elif "=" in t and ("(" in t or "[" in t or "{" in t):
            is_code = True
            
        if is_code:
            current.append(t)
        else:
            if current:
                code.append(current)
                current = []
    if current:
        code.append(current)
        
    with open('code_blocks.json', 'w', encoding='utf-8') as f:
        json.dump(code, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    extract_code(r"C:\Users\irena\Downloads\GLAVA_4.docx")
