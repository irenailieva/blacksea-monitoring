```markdown
# Project Specification: Black Sea Monitoring System (Frontend)

## 1. Role & Objective
Act as a Senior Frontend Engineer. Your goal is to build the client-side of a satellite monitoring system. The system detects algae blooms in the Black Sea using Sentinel-2 data and Machine Learning.

## 2. Tech Stack
- **Framework:** React 18 (Vite) + TypeScript
- **Styling:** Tailwind CSS + shadcn/ui (use Lucide React for icons)
- **Maps:** react-leaflet (v4+) + leaflet
- **State Management:** Zustand (preferred) or React Context
- **Networking:** Axios (Must use interceptors for JWT refresh logic)
- **Routing:** React Router DOM (v6+)

## 3. Backend Data Structures (Domain Models)
*The backend is FastAPI + PostGIS. Use these TypeScript interfaces which match the database schema exactly:*

```typescript
// derived from table "user"
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'viewer' | 'analyst' | 'admin';
  // Auth fields (usually handled internally but present in DB schema)
  refresh_token?: string; 
  refresh_token_expires_at?: string; // ISO timestamp
}

// derived from table "region"
export interface Region {
  id: number;
  name: string;
  description: string;
  type: 'aoi' | string; // Default is 'aoi' (Area of Interest)
  geometry: GeoJSON.Polygon; // PostGIS GEOMETRY
}

// derived from table "scene"
export interface Scene {
  id: number;
  sentinel_id: string; // e.g., "S2A_MSIL2A_2023..."
  acquired_at: string; // ISO timestamp
  cloud_coverage: number; // decimal(5,2)
  region_id: number;
}

// derived from table "classification_result"
export interface ClassificationResult {
  id: number;
  scene_id: number;
  label: 'vegetation' | 'sand' | 'water' | 'other';
  area_m2: number;
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon; 
}

```

## 4. API Endpoints Contract

Assume the backend provides these endpoints:

* `POST /auth/login` -> Returns `{ access_token: string, refresh_token: string, token_type: "bearer" }`
* `POST /auth/refresh` -> Accepts `{ refresh_token: string }`. Returns `{ access_token: string, refresh_token: string }`
* `GET /users/me` -> Returns `User`
* `GET /regions` -> Returns `Region[]`
* `GET /scenes` -> Accepts query params `?region_id=X&start_date=YYYY-MM-DD`. Returns `Scene[]`
* `GET /analysis/results/{scene_id}` -> Returns GeoJSON FeatureCollection of classification results.

## 5. Implementation Plan (Step-by-Step)

Please implement the solution following these steps. **Wait for my confirmation after each step.**

### Step 1: Foundation & Auth (With Refresh Logic)

* Set up the **Axios instance**:
* **Request Interceptor:** Inject the `Bearer` token from localStorage.
* **Response Interceptor:** Handle `401 Unauthorized` errors. If a 401 occurs, attempt to call `/auth/refresh` using the stored refresh token. If successful, retry the original failed request. If refresh fails, log the user out.


* Create an `useAuth` store (Zustand) to manage `user`, `accessToken`, and `refreshToken`.
* Create a simple Login Page.

### Step 2: App Layout (Dashboard Shell)

* Create a standard layout with:
* **Sidebar (Left):** For filters.
* **Header (Top):** Logo and User Profile menu.
* **Main Content:** This will hold the Map.


* Use `shadcn/ui` components for the structure.

### Step 3: Interactive Map Component

* Implement the `MapContainer` from `react-leaflet`.
* **Base Layer:** Use OpenStreetMap or Esri Satellite.
* **Regions Layer:** Fetch `Region[]` and draw them as blue outlines.
* *Note:* Use the `type` field to potentially style them differently (though currently all are 'aoi').



### Step 4: Connecting the Flow

* In the Sidebar, when a user selects a Region and Date, fetch the matching `Scenes`.
* Display the scenes in a list.
* When a user clicks a `Scene`, fetch its `ClassificationResults`.
* Overlay the results on the map:
* Color **Green** (#00FF00) for 'vegetation' (algae).
* Color **Yellow** for 'sand'.
* Add tooltips showing `area_m2`.



---

**Instruction to Agent:**
Start by analyzing this specification. Then, generate the code for **Step 1 (Foundation & Auth)** focusing on the robust Axios interceptor logic.

```

```