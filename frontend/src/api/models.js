/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} email
 * @property {'viewer' | 'analyst' | 'admin'} role
 * @property {{default_region_id: number, notifications: boolean}} [preferences]
 */

/**
 * @typedef {Object} Team
 * @property {number} id
 * @property {string} name
 * @property {User[]} members
 */

/**
 * @typedef {Object} Region
 * @property {number} id
 * @property {string} name
 * @property {Object} geometry - GeoJSON Polygon
 * @property {'aoi'} type
 */

/**
 * @typedef {Object} Scene
 * @property {number} id
 * @property {string} sentinel_id
 * @property {string} acquired_at - ISO Date
 * @property {number} cloud_coverage
 * @property {'pending' | 'processing' | 'completed' | 'failed'} etl_status
 */

/**
 * @typedef {Object} ClassificationResult
 * @property {number} id
 * @property {number} scene_id
 * @property {'vegetation' | 'sand' | 'water'} label
 * @property {number} area_m2
 * @property {Object} geometry - GeoJSON Polygon
 */

/**
 * @typedef {Object} ShapValue
 * @property {string} feature_name
 * @property {number} importance_value
 */

export const ROLES = {
  VIEWER: 'viewer',
  ANALYST: 'analyst',
  ADMIN: 'admin',
};

export const SCENE_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
};
