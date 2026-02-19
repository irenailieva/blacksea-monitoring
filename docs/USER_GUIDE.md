# Black Sea Monitoring System: User Guide

Welcome to the **Black Sea Aquatic Monitoring System**. This guide provides an end-to-end overview of the system's features, designed to help analysts and viewers monitor underwater vegetation, algae, and coastal changes using satellite data and machine learning.

---

## 1. Getting Started: Authentication

### Login & Security
- **Access**: Secure access is provided via the Login screen.
- **Security**: The system uses **HttpOnly Secure Cookies** for authentication. You do not need to manage tokens manually; the browser handles this automatically.
- **Theme**: Enjoy a "Premium Aquatic" light theme designed for maximum readability during long analysis sessions.

---

## 2. Map Dashboard (Core Monitoring)

The Map Dashboard is the heart of the system, where you visualize geographical data and classification results.

### Navigation & Base Layers
- **Interchangeable Maps**: Use the layer control (top right) to switch between:
  - **OpenStreetMap**: Standard street-level data.
  - **Satellite (Esri)**: High-resolution orbital imagery.
  - **Hydrography (Esri Ocean)**: Detailed bathymetric and oceanic data.
- **Interactive Markers**: Sea markers (OpenSeaMap) can be toggled to aid coastal navigation.

### Regions & Classification
- **AOIs (Areas of Interest)**: Selected regions like "Varna Bay" are highlighted with blue outlines. Click a region to see its metadata.
- **ML Overlays**: When a scene is selected, the **Classification Overlay** renders:
  - **Green**: Vegetation / Algae detection.
  - **Yellow**: Sand / Coastal sediment.
- **Quick Stats**: Click any classified polygon to see the exact **Area (m²)** calculated by the ML ensemble.

### Filtering
- Search for specific satellite scenes based on **Date Range**, **Cloud Coverage %**, and **Water Depth**.

---

## 3. Analysis Dashboard (Insights)

Transform raw data into actionable insights using advanced visualization tools.

### Vegetation Trends
- **Temporal Analysis**: View line charts showing the fluctuation of vegetation area over months or years for a specific region.
- **Seasonality**: Identify seasonal patterns in algae blooms.

### AI Explainability (SHAP)
- **Feature Importance**: Understand *why* the AI classified a specific area as vegetation.
- **Shapley Values**: Interactive bar charts show which spectral bands (NDWI, Blue, NIR, etc.) contributed most to the prediction.

### Data Export
- Generate reports in **PDF** or **CSV** format for external stakeholder presentations.

---

## 4. Data Management & ETL

### Manual Uploads
- **GPS/Drone Data**: Upload GPS point sets or Drone Orthomosaics (.GeoTIFF) directly via the **Data** page.
- **Validation**: The system automatically validates spatial tags before processing.

### ETL Monitoring
- **Real-time Status**: Monitor the status of Sentinel-2 data processing (ETL) through status badges:
  - `Pending`: In queue.
  - `Processing`: ML extraction in progress.
  - `Completed`: Data ready for visualization.
  - `Failed`: Error log available for admins.

---

## 5. Notifications & Alerts

Keep track of critical changes without staying glued to the screen.

### Bell Alerts
- Click the **Bell Icon** in the header to see:
  - **Ecological Alerts**: Significant drops (>20%) in vegetation coverage.
  - **System Updates**: New satellite scenes available for your region.
  - **Task Completion**: Notification when a manual upload or ETL process finishes.

---

## 6. Admin Controls

*(Admin role only)*

### Team Management
- Add or remove users from specific project groups (e.g., "Research Team Alpha").
- Manage user roles: **Viewer**, **Analyst**, or **Admin**.

### System Health
- Monitor the connectivity between the **FastAPI Gateway**, the **XGBoost/LightGBM ML Service**, and the **PostGIS Database**.

---

> [!TIP]
> **Pro Tip**: Use the **Satellite (Esri)** base layer alongside the **Vegetation Overlay** to visually confirm AI predictions against real-world imagery.
