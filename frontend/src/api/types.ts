/**
 * Интерфейси за потребители и автентикация (User & Auth Interfaces)
 * Дефинират структурата на данните, получавани от сървъра.
 */

// Представя модела на потребител в системата
export interface User {
    id: number; // Уникален идентификатор в базата данни
    username: string; // Потребителско име
    email?: string; // Имейл адрес (по избор)
    role: 'viewer' | 'researcher' | 'admin'; // Ролеви модел за контрол на достъпа (RBAC)
    preferences?: {
        default_region_id: number; // Регион по подразбиране при зареждане на картата
        notifications: boolean; // Дали потребителят иска да получава известия
    };
}

// Представя екип (Team), съдържащ група потребители (напр. за съвместна работа)
export interface Team {
    id: number;
    name: string; // Име на екипа
    members: User[]; // Списък с членовете на екипа
}

/**
 * Географски интерфейси (Geography & Map Interfaces)
 */

// Представя Зона на интерес (Area of Interest - AOI) или географски регион
export interface Region {
    id: number;
    name: string; // Име на региона (напр. "Варненски залив")
    geometry: GeoJSON.Polygon; // Геометрични координати във формат GeoJSON
    type: 'aoi'; // Тип на обекта
}

/**
 * Интерфейси за сателитни данни (Satellite Data Interfaces)
 */

// Представя сателитна снимка (сцена) от Sentinel-2
export interface Scene {
    id: number;
    scene_id: string; // Уникален идентификатор от Sentinel
    display_name?: string; // Човешки-четимо име
    acquisition_date: string; // Дата на заснемане (ISO Date String)
    cloud_cover?: number; // Процент облачно покритие (0-100)
    satellite: string; // Име на сателита (напр. 'Sentinel-2A')
    tile?: string; // Идентификатор на плочката (MGRS tile)
    region_id: number; // Към кой регион принадлежи
    created_at?: string; // Време на добавяне в базата
    updated_at?: string; // Време на последна модификация
}

/**
 * Интерфейси за резултати от анализи (Analysis Result Interfaces)
 */

// Представя резултата от класификационен ML модел
export interface ClassificationResult {
    id: number;
    scene_id: number; // Идентификатор на сцената, от която е генериран резултатът
    label: 'vegetation' | 'sand' | 'water'; // Клас на обекта (напр. растителност, пясък, вода)
    area_m2: number; // Изчислена площ в квадратни метри
    geometry: GeoJSON.Polygon; // Геометрични граници на класифицирания обект за визуализация на картата
}

// Представя стойност на SHAP (SHapley Additive exPlanations) за обяснимост на ML модела
export interface ShapValue {
    feature_name: string; // Име на характеристиката (напр. NDWI, B04, B08)
    importance_value: number; // Стойност на важността (колко е повлияла на предвиждането)
}
