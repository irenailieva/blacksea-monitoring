---
trigger: always_on
---

# Project Specification: Black Sea Aquatic Monitoring System

## 1. Role & Objective
Act as a Senior Frontend Engineer. Your goal is to build the web interface for a system that maps aquatic parameters (underwater vegetation, algae) along the Bulgarian coast. The system uses Sentinel-2 satellite data, corrected and classified via ML ensembles (XGBoost/LightGBM).

## 2. Tech Stack
- **Framework:** React 18 (Vite) + TypeScript
- **Styling:** Tailwind CSS + shadcn/ui (Radix Primitives)
- **Icons:** Lucide React
- **Maps:** react-leaflet (v4+) + leaflet. (Must support multiple base layers: OSM, Satellite).
- **Charts:** Recharts (for temporal analysis and SHAP values).
- **State Management:** Zustand.
- **Networking:** Axios.
- **Routing:** React Router DOM (v6+).

## 3. Architecture & Data Flow
- **Pattern:** Three-layer web app. React communicates with a **FastAPI Gateway**.
- **Auth:** JWT Access Tokens are stored in **HttpOnly cookies**.
  - *Crucial:* The frontend does NOT store tokens in LocalStorage. Axios must be configured with `withCredentials: true`.
- **Real-time:** WebSockets (or polling) used for ETL status updates and Notifications.

## 4. Domain Models (TypeScript Interfaces)

```typescript
// User & Auth
export interface User {
  id: number;
  email: string;
  role: 'viewer' | 'analyst' | 'admin';
  preferences?: { default_region_id: number; notifications: boolean };
}

// Teams
export interface Team {
  id: number;
  name: string;
  members: User[];
}

// Geography
export interface Region {
  id: number;
  name: string; // e.g., "Varna Bay"
  geometry: GeoJSON.Polygon;
  type: 'aoi'; 
}

// Satellite Data
export interface Scene {
  id: number;
  sentinel_id: string;
  acquired_at: string; // ISO Date
  cloud_coverage: number;
  etl_status: 'pending' | 'processing' | 'completed' | 'failed';
}

// Analysis Results
export interface ClassificationResult {
  id: number;
  scene_id: number;
  label: 'vegetation' | 'sand' | 'water';
  area_m2: number;
  geometry: GeoJSON.Polygon; // The colored overlay
}

// ML Explainability
export interface ShapValue {
  feature_name: string; // e.g., "NDWI", "Blue_Band"
  importance_value: number;
}

```

## 5. Functional Requirements (Screens & Features)

### A. Authentication

* Login screen.
* Handle HttpOnly cookie flow (Axios interceptors for 401 response -> redirect to login).

### B. Map Dashboard (Main Screen)

* **Base Layers:** Toggle between OpenStreetMap, Satellite (Esri/Google), and Hydrography.
* **Filters:** Date Range, Cloud Coverage (<%), Depth.
* **Overlays:**
* Regions (AOI) outlines.
* Classification polygons (Green for vegetation, Yellow for sand).


* **Interaction:** Clicking a polygon shows a popup with area size and properties.

### C. Analysis Dashboard

* **Charts:** Line chart showing "Vegetation Area (m²)" over years/seasons for a selected region.
* **Explainability:** Bar chart showing SHAP values (feature importance) for specific classification results.
* **Export:** Button to export current view/report as PDF or CSV.

### D. Data & Admin

* **Manual Upload:** UI to upload GPS points or Drone Orthomosaics (GeoTIFF).
* **ETL Monitor:** Visual indicator (progress bar or status badge) for currently processing Sentinel-2 scenes.
* **Team Management:** (Admin only) Add/Remove users from project groups.

### E. Notifications

* UI element (bell icon) to show alerts:
* Drop in vegetation coverage > 20%.
* New scene available.
* ETL process finished.

## 6. Implementation Plan (Step-by-Step)

**Wait for my confirmation after each step.**

### Step 1: Foundation & Secure Auth

* Setup Axios with `withCredentials: true` to handle HttpOnly cookies.
* Create `useAuth` store (Zustand) to fetch `GET /users/me` on app load.
* Implement Login Page.

### Step 2: Main Layout & Navigation

* Sidebar: Links to "Map", "Analysis", "Data/Uploads", "Admin".
* Header: User Profile, Team Switcher, Notification Bell.
* Use `shadcn/ui` components.

### Step 3: Advanced Map Component

* Implement `MapContainer` with `LayersControl` (Base maps).
* Fetch and display `Regions`.
* Implement side panel for filtering Scenes (Date, Cloud %).

### Step 4: Analysis & Charts

* Create the "Analysis" page.
* Implement `Recharts` to visualize dummy data (until API is ready) for vegetation trends.
* Implement SHAP visualization component.

### Step 5: Admin & Data Operations

* Create File Upload component for manual GeoTIFFs.
* Create Team Management table.