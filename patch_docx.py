import docx
import re

def patch_docx(path):
    doc = docx.Document(path)
    
    for p in doc.paragraphs:
        text = p.text
        if not text.strip():
            continue
            
        # 1. scenes table: Remove sun_azimuth/sun_elevation and footprint paragraphs
        if "Атрибутите sun_azimuth и sun_elevation описват точната позиция на слънцето" in text:
            p.text = "Таблицата scenes съхранява базова информация за сателитните изображения (дата на заснемане, облачност, път към данните), необходима за анализите."
        if "Атрибутът footprint използва PostGIS типа GEOMETRY" in text:
            p.text = "Връзката с конкретната географска област се осъществява чрез релация към таблицата regions, което оптимизира структурата, избягвайки дублиране на полигони за всяка сцена."
            
        # 2. classification_results: Remove GEOMETRY and ST_Area claims
        if "Тук се съхраняват векторизираните резултати от анализите на машинното обучение. Всеки запис представлява конкретен полигон" in text:
            p.text = "Тук се съхраняват агрегираните резултати от анализите на машинното обучение за всяка сцена и регион. Всеки запис съдържа класификационен етикет (растителност, пясък, вода) и съответната изчислена площ (area_m2)."
        if "Изчисляването на площта (area_ha) се извършва в базата данни чрез функцията ST_Area" in text:
            p.text = "Площта (area_m2) се записва директно като числена стойност в квадратни метри по време на изпълнение на ML модела, което елиминира нуждата от тежки пространствени SQL изчисления в реално време."
            
        # 3. Spatial indexing
        if "За всички геометрични колони в таблиците scenes, classification_results и regions са създадени пространствени индекси от тип GiST" in text:
            p.text = "В системата пространствената геометрия се съхранява централизирано в таблицата regions. Върху нея е създаден пространствен индекс от тип GiST (Generalized Search Tree)."
            
        # 4. DVC
        if "Интеграцията с DVC (Data Version Control) позволява на базата данни да съхранява само леките метаданни" in text:
            p.text = "За съхранение на тежките растерни оригинали от тип GeoTIFF, системата разчита на локалната файлова система, като пътищата до тях се записват в свързаната таблица scene_files. Това разделя метаданните от същинските растери, запазвайки базата данни лека и бърза."
            
        # 5. Frontend versions
        if "React 18" in text:
            p.text = p.text.replace("React 18", "React 19")
        if "react-router-dom v6" in text:
            p.text = p.text.replace("react-router-dom v6", "react-router-dom v7")
        if "react-leaflet v4" in text:
            p.text = p.text.replace("react-leaflet v4", "react-leaflet v5")
            
    doc.save(path)
    print("Patched document successfully.")

if __name__ == "__main__":
    patch_docx(r"C:\Users\irena\Downloads\GLAVA_4.docx")
