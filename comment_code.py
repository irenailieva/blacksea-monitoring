import docx
import re

def is_code(text):
    text = text.strip()
    if not text:
        return False
    if text.startswith(('# ', '//', '/*', '*/', 'import ', 'export ', 'def ', 'class ', 'const ', 'let ', '<', 'ST_', '@', 'module.exports', 'rf =', 'xgb_model =', 'lgb_model =', 'X_train', 'prob1 =', 'avg_prob =', 'final_pred =', 'yhat =', 'return ', 'user: ', 'isLoading: ', 'error: ', '...', 'id:', 'read:', 'timestamp:', 'notifications:', 'unreadCount:', '{ name:', 'item =>', 'baseURL:', 'headers:', 'content:', 'theme:', 'plugins:', '--', 'job.status', 'size=', 'variant=', 'className=', 'const [', 'api.get', '])', 'const csv', 'const blob', 'clearInterval', 'const newRes', 'const newest', 'if (newest)', 'with rasterio.open', 'geometry_element =', 'new_region =', 'payload =', 'updated_at =', 'class_weight=', 'objective=', 'tree_method=')) or text.endswith(('{', '}', ';', '/>', '",', "',", "')", "]")):
        # Skip math formulas and regular bullet points
        if text.startswith('$') or text.startswith('- '):
            return False
        return True
    if "=" in text and ("(" in text or "[" in text or "{" in text):
        return True
    return False

replacements = [
    # 1
    (["ST_Area(ST_Transform(geom, 32635))"],
     ["ST_Area(ST_Transform(geom, 32635)) -- Изчисляване на площта в UTM зона 35N"]),
     
    # 2
    (["ALTER TABLE classification_results ADD CONSTRAINT check_valid_geom CHECK (ST_IsValid(geom));"],
     ["ALTER TABLE classification_results ADD CONSTRAINT check_valid_geom CHECK (ST_IsValid(geom)); -- Добавяне на ограничение за валидна геометрия"]),
     
    # 3 ACOLITE
    (["def preprocess_raster", "with rasterio.open"],
     ["def preprocess_raster(input_path: str) -> str: # Дефиниране на функция за обработка",
      "    # ... (съкратена базова обработка с rasterio) # Изпълнение на логика",
      "    return output_path # Връщане на обработения файл"]),
      
    # 4 Numpy
    (["def generate_index", "with rasterio.open"],
     ["def generate_index(raster_path: str, index_name: str = 'NDVI') -> str: # Дефиниране на функция за индекси",
      "    # ... (съкратени изчисления с NumPy масиви) # Изпълнение на векторни операции",
      "    return output_path # Връщане на изчисления индекс"]),
      
    # 5 uploader
    (["geometry_element =", "new_region ="],
     ["geometry_element = WKTElement(wkt_geom, srid=4326) # Инстанциране на обект с PostGIS геометрия",
      "new_region = Region(name=aoi_config[\"name\"], geometry=geometry_element) # Инициализиране на нов регион"]),
      
    # 6 pipeline
    (["payload =", "updated_at ="],
     ["payload = jsonb_set(COALESCE(payload, '{}'), '{progress}', :prog), -- Обновяване на JSONB поле с прогрес",
      "updated_at = NOW() -- Задаване на текущо време за одит"]),
      
    # 7 RF
    (["rf = RandomForestClassifier"],
     ["rf = RandomForestClassifier( # Инициализация на модела Random Forest",
      "    class_weight='balanced', # Балансиране на класовете срещу дисбаланс",
      ") # Край на инициализацията"]),
      
    # 8 XGB
    (["xgb_model = xgb.XGBClassifier"],
     ["xgb_model = xgb.XGBClassifier( # Инициализация на модела XGBoost",
      "    objective='multi:softmax', # Задаване на многокласова класификация",
      "    tree_method=\"hist\", # Използване на хистограмен метод за бързина",
      ") # Край на инициализацията"]),
      
    # 9 LGB
    (["lgb_model = lgb.LGBMClassifier"],
     ["lgb_model = lgb.LGBMClassifier( # Инициализация на модела LightGBM",
      "    class_weight='balanced' # Балансиране на класовете",
      ") # Край на инициализацията"]),
      
    # 10 Train test split
    (["X_train, X_test, y_train, y_test = train_test_split("],
     ["X_train, X_test, y_train, y_test = train_test_split( # Разделяне на данните на обучаващо и тестово множество",
      "    X, y, test_size=0.2, stratify=y # Запазване на пропорциите на класовете (stratify)",
      ") # Край на функцията"]),
      
    # 11 vote
    (["def _vote", "avg_prob", "final_pred"],
     ["def _vote(self, X): # Дефиниция на функция за меко гласуване (Soft Voting)",
      "    avg_prob = (self.rf.predict_proba(X) + self.xgb.predict_proba(X) + self.lgb.predict_proba(X)) / 3.0 # Усредняване",
      "    return np.argmax(avg_prob, axis=1) # Връщане на класа с най-висока средна вероятност"]),
      
    # 12 SHAP
    (["feature_names =", "shap.summary_plot"],
     ["feature_names = ['Blue', 'Green', 'Red', 'NIR', 'NDVI', 'NDWI'] # Дефиниране на спектралните характеристики",
      "shap.summary_plot(shap_values[1], X_test, feature_names=feature_names) # Генериране на визуална SHAP графика"]),
      
    # 13 FastAPI
    (["@app.post", "def infer_batch("],
     ["@app.post(\"/infer_batch\") # Дефиниране на POST маршрут за класификация",
      "def infer_batch(req: PredictBatchRequest): # Дефиниране на функция за обработка",
      "    return PredictBatchResponse(yhat=model.predict_batch(req.batch)) # Връщане на предсказанията"]),
      
    # 14 Zustand Auth
    (["user: null,", "isLoading:"],
     ["user: null, // Начална стойност за липса на удостоверен потребител",
      "isLoading: true, // Флаг, указващ текущо зареждане на данните",
      "error: null, // Поле за съхранение на потенциални грешки"]),
      
    # 15 Zustand Notifications
    (["read: false,", "timestamp:", "unreadCount:"],
     ["id: Date.now(), // Генериране на уникален идентификатор",
      "read: false, // Задаване на статус по подразбиране като непрочетено",
      "timestamp: new Date().toISOString(), // Създаване на времеви печат",
      "unreadCount: updated.filter(i => !i.read).length // Динамично изчисляване на брояча"]),
      
    # 16 Router
    (["{ name:", "href:", "role:"],
     ["{ name: 'Map', href: '/', icon: Map }, // Дефиниране на линк към главната карта",
      "{ name: 'Analysis', href: '/analysis', icon: LayoutDashboard }, // Дефиниране на линк към анализите",
      "{ name: 'Admin', href: '/admin', icon: Users, role: 'admin' }, // Дефиниране на линк с ограничение за администратори"]),
      
    # 17 Tailwind JS
    (["content:", "theme:", "plugins:"],
     ["content: [\"./index.html\", \"./src/**/*.{js,ts,jsx,tsx}\"], // Задаване на пътищата за сканиране на CSS класове",
      "theme: { extend: {} }, // Обект за разширяване на стандартната тема",
      "plugins: [], // Масив за добавяне на допълнителни функционалности"]),
      
    # 18 Tailwind CSS
    (["--color-aquatic", "algae:"],
     ["--color-aquatic-deep: #0f172a; /* Дефиниране на тъмносин фон за интерфейса */",
      "--color-aquatic-algae: #22c55e; /* Дефиниране на зелен цвят за детекция на водорасли */",
      "--color-aquatic-sand: #eab308; /* Дефиниране на жълт цвят за пясъчни дъна */"]),
      
    # 19 Tailwind classes JS
    (["job.status ==="],
     ["job.status === 'failed' ? 'border-destructive/30 bg-destructive/5' : // Прилагане на червен стил при грешка",
      "job.status === 'completed' ? 'border-green-500/30 bg-green-500/5' : // Прилагане на зелен стил при успех",
      "'' // Стил по подразбиране за всички останали случаи"]),
      
    # 20 Button
    (["variant=\"outline\"", "className="],
     ["size=\"sm\" // Задаване на малък размер на бутона",
      "variant=\"outline\" // Използване на контурен вариант без запълване",
      "className=\"h-5 px-2 border-destructive/40 hover:bg-destructive/10\" // Добавяне на допълнителни CSS класове за състояния"]),
      
    # 21 Promise.all
    (["const [regionsRes", "Promise.all"],
     ["const [regionsRes, scenesRes] = await Promise.all([ // Иницииране на паралелно изчакване на заявките",
      "    api.get<Region[]>('/regions?with_geometry=true'), // Заявка за извличане на геометриите",
      "    api.get<Scene[]>('/scenes'), // Заявка за извличане на сателитните сцени",
      "]); // Край на паралелното изпълнение"]),
      
    # 22 Blob CSV
    (["const csvContent", "const blob"],
     ["const csvContent = [headers.join(\",\"), ...rows.map(r => r.join(\",\"))].join(\"\\n\"); // Форматиране на данните в CSV низ",
      "const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' }); // Създаване на двоичен обект за изтегляне"]),
      
    # 23 JSX div
    (["<div className=\"grid"],
     ["<div className=\"grid h-full grid-cols-1 gap-4 lg:grid-cols-4\"> {/* Създаване на основната адаптивна решетка */} ",
      "    <div className=\"space-y-4 lg:col-span-1 overflow-y-auto pr-1\"> {/* Обособяване на левия страничен панел */} "]),
      
    # 24 Polling
    (["const interval", "setInterval"],
     ["const interval = setInterval(async () => { // Стартиране на периодичен интервал за проверка",
      "    const res = await api.get('/scenes/etl-status'); // Извличане на актуалния статус на задачите",
      "    if (res.data.find(j => j.id === activeJob.job_id)?.status === 'completed') { // Проверка дали специфичната задача е завършила",
      "        clearInterval(interval); // Спиране на интервала при успех",
      "    } // Край на проверката",
      "}, 3000); // Повтаряне на заявката на всеки 3 секунди"])
]

def format_doc(path):
    doc = docx.Document(path)
    
    # 1. First, identify all code blocks (contiguous runs of is_code)
    blocks = []
    current_block = []
    for p in doc.paragraphs:
        if is_code(p.text):
            current_block.append(p)
        else:
            if current_block:
                blocks.append(current_block)
                current_block = []
    if current_block:
        blocks.append(current_block)
        
    # 2. For each block, find the best replacement
    for b in blocks:
        text_joined = " ".join([p.text for p in b])
        best_match = None
        for keys, lines in replacements:
            if all(k in text_joined for k in keys):
                best_match = lines
                break
                
        if best_match:
            # We matched a replacement!
            # Replace the first paragraph with the first line, etc.
            # Remove any extra paragraphs.
            for i, p in enumerate(b):
                if i < len(best_match):
                    p.text = best_match[i]
                    p.style = 'Normal'  # You can apply a code style if it exists, but keeping default is safer
                    # to make it look like code we could just set font but python-docx run manipulation is needed for font
                else:
                    # Remove excess paragraph
                    if p._element.getparent() is not None:
                        p._element.getparent().remove(p._element)
                        
            # If the best_match has MORE lines than the original block, we add them (insert after the last one)
            if len(best_match) > len(b):
                last_p = b[-1]
                for extra_line in best_match[len(b):]:
                    new_p = last_p.insert_paragraph_before(extra_line)
                    # wait, insert_paragraph_before adds before. We can just add after by navigating XML, 
                    # but python-docx doesn't have insert_after directly easily.
                    # It's better to just reuse paragraphs or add at the end of the document? No, it must be inline.
                    # Actually, we can just put multiple lines in the last paragraph separated by \n.
                    # Let's do that!
                    pass
                
                # simpler approach: just join the remaining lines with \n and put in the last paragraph
                last_p = b[-1]
                last_p.text = "\n".join([last_p.text] + best_match[len(b):])
                last_p.style = 'Normal'
        else:
            # If we didn't explicitly map it, we just add "// код" or "# код" to every line.
            # Wait, let's see if we missed any.
            # We can do a fallback:
            for p in b:
                if not p.text.strip(): continue
                # if it already has a comment, skip
                if "//" in p.text or "# " in p.text or "/*" in p.text or "--" in p.text:
                    continue
                # heuristic: if python
                if "def " in p.text or "import " in p.text:
                    p.text = p.text + " # Дефиниция"
                elif "{" in p.text or "const" in p.text or "let" in p.text:
                    p.text = p.text + " // Изпълнение"
                else:
                    p.text = p.text + " // Код"

    doc.save(path)
    print("Formatted code blocks successfully.")

if __name__ == "__main__":
    format_doc(r"C:\Users\irena\Downloads\GLAVA_4.docx")
