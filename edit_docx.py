import docx

def replace_in_paragraph(p, old, new):
    if old in p.text:
        # To preserve formatting as much as possible, we replace text in runs
        # But if a word is split across runs, it's hard. 
        # A simpler approach: if we don't care too much about intra-word formatting,
        # we can just replace p.text, which clears runs and adds one new run.
        # Given this is a thesis, preserving styles is important, but for structural 
        # changes, we might just replace p.text. Let's try simple p.text replacement
        # for whole paragraphs if it's a code block, otherwise string replacement on p.text.
        pass

def process_doc():
    doc = docx.Document(r"C:\Users\irena\Downloads\GLAVA_4.docx")
    
    replacements = {
        "sentinel_scenes": "scenes",
        "vegetation_detections": "classification_results",
        "spectral_indices_stats": "index_values",
        "aoi_zones": "regions",
        "alerts": "notifications",
        "mlflow_runs": "model_runs",
        "SentinelScene": "Scene",
        "VegetationDetection": "ClassificationResult",
        "същността AOI": "същността Region",
        "същността Alert": "същността Notification"
    }

    acolite_code = """# Логика за интеграция на ACOLITE (Dark Spectrum Fitting)
def apply_acolite_correction(input_bundle, output_dir):
    import subprocess
    # Конфигурация на параметрите за българската акватория
    settings = {
        'limit': '42.0,27.0,43.5,29.0', # Примерни граници
        'dsf_aot_estimate': 'fixed',
        'l2w_parameters': ['rhow_*', 'ndwi']
    }
    # Изпълнение на ACOLITE като външен процес
    subprocess.run(["python", "acolite.py", "--settings", "settings.txt"])"""

    rasterio_code = """def preprocess_raster(input_path: str) -> str:
    # Базова обработка с rasterio
    output_path = input_path.replace(".tif", "_processed.tif")
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read()
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(data)
            for i in range(1, src.count + 1):
                dst.set_band_description(i, src.descriptions[i-1])
    return output_path"""

    polars_code = """# Мързеливо (lazy) зареждане на данните
df = pl.scan_csv(csv_path)

# Векторизирано изчисляване на индекси
df = df.with_columns([
((pl.col("nir") - pl.col("red")) / (pl.col("nir") + pl.col("red"))).alias("NDVI"),
((pl.col("green") - pl.col("nir")) / (pl.col("green") + pl.col("nir"))).alias("NDWI")
])
    
# Филтриране и агрегация в паметта
result = df.filter(pl.col("NDVI") > 0.1).collect()
return result"""

    numpy_code = """def generate_index(raster_path: str, index_name: str = 'NDVI') -> str:
    output_path = raster_path.replace(".tif", f"_{index_name}.tif")
    with rasterio.open(raster_path) as src:
        red = src.read(3).astype('float32')
        nir = src.read(4).astype('float32')
        
        epsilon = 1e-10
        ndvi = (nir - red) / (nir + red + epsilon)
        
        profile = src.profile
        profile.update(dtype=rasterio.float32, count=1, driver='GTiff')
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(ndvi, 1)
            dst.set_band_description(1, index_name)
    return output_path"""

    for p in doc.paragraphs:
        # Simple replacements
        for k, v in replacements.items():
            if k in p.text:
                # We replace the text of the whole paragraph. This removes inline styling (bold/italic).
                # But it is the safest way to replace without dealing with run splits.
                # Let's preserve the paragraph style.
                style = p.style
                text = p.text.replace(k, v)
                p.text = text
                p.style = style

        # Replace ACOLITE section
        if "Извличане на данни и атмосферна корекция с ACOLITE" in p.text:
            p.text = p.text.replace("Извличане на данни и атмосферна корекция с ACOLITE", "Извличане на данни и базова предварителна обработка")
        if "В работния поток на preprocessor.py е заложена логика за изпълнение на специализираната корекция" in p.text:
            p.text = "В работния поток на preprocessor.py е заложена логика за базова предварителна обработка чрез rasterio:"
        if "Използването на метода \"Dark Spectrum Fitting\" (DSF) в ACOLITE" in p.text:
            p.text = "Системата в момента използва базова обработка с rasterio, като запазва оригиналните спектрални канали за последващ анализ."

        # Replace Polars section
        if "Оптимизация на процеса чрез Polars" in p.text:
            p.text = p.text.replace("Оптимизация на процеса чрез Polars", "Оптимизация на процеса чрез Rasterio и NumPy")
        if "Имплементацията залага на библиотеката Polars" in p.text:
            p.text = "Имплементацията залага на библиотеките Rasterio и NumPy за постигане на максимална производителност при генериране на индекси:"
        if "Функцията scan_csv създава план за изпълнение" in p.text:
            p.text = "Използването на векторизирани операции с NumPy върху масиви, прочетени чрез Rasterio, позволява изключително бързо изчисляване на спектрални индекси върху милиони пиксели, съкращавайки времето за подготовка на данни."

        # Replace Code Blocks
        if "apply_acolite_correction" in p.text:
            p.text = rasterio_code
        if "pl.scan_csv" in p.text:
            p.text = numpy_code
            
        # Additional cleanup of code lines if they were split in multiple paragraphs
        if "subprocess.run" in p.text and "acolite" in p.text:
            p.text = ""
        if "df.with_columns" in p.text or "pl.col" in p.text or "result = df.filter" in p.text:
            p.text = ""

    doc.save(r"C:\Users\irena\Downloads\GLAVA_4.docx")
    print("Done editing docx")

if __name__ == "__main__":
    process_doc()
