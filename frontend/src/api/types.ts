/**
 * User & Auth Interfaces
 */
export interface User {
    id: number;
    username: string;
    email?: string;
    role: 'viewer' | 'analyst' | 'admin';
    preferences?: {
        default_region_id: number;
        notifications: boolean;
    };
}

export interface Team {
    id: number;
    name: string;
    members: User[];
}

/**
 * Geography & Map Interfaces
 */
export interface Region {
    id: number;
    name: string;
    geometry: GeoJSON.Polygon;
    type: 'aoi';
}

/**
 * Satellite Data Interfaces
 */
export interface Scene {
    id: number;
    scene_id: string;
    acquisition_date: string; // ISO Date String
    cloud_cover?: number;
    satellite: string;
    tile?: string;
    region_id: number;
    created_at?: string;
    updated_at?: string;
}

/**
 * Analysis Result Interfaces
 */
export interface ClassificationResult {
    id: number;
    scene_id: number;
    label: 'vegetation' | 'sand' | 'water';
    area_m2: number;
    geometry: GeoJSON.Polygon;
}

export interface ShapValue {
    feature_name: string;
    importance_value: number;
}
