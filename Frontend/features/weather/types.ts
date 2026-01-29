/**
 * Weather Feature - Type Definitions
 *
 * Core types for weather simulation, forecasting, and grid data
 * Supports real-time weather grid visualization and alert system
 */

/**
 * Weather grid cell data point
 *
 * Represents a single grid cell in the weather simulation
 * Contains various weather parameters at a specific location
 */
export interface WeatherGridCell {
  /**
   * Unique identifier for grid cell
   */
  id: string;

  /**
   * Latitude coordinate of cell center
   */
  latitude: number;

  /**
   * Longitude coordinate of cell center
   */
  longitude: number;

  /**
   * Temperature in Celsius
   */
  temperature: number;

  /**
   * Relative humidity (0-100%)
   */
  humidity: number;

  /**
   * Precipitation rate (mm/h)
   */
  precipitation: number;

  /**
   * Wind speed (m/s)
   */
  windSpeed: number;

  /**
   * Wind direction (degrees, 0-360)
   */
  windDirection: number;

  /**
   * Atmospheric pressure (hPa)
   */
  pressure: number;

  /**
   * Cloud coverage (0-100%)
   */
  cloudCoverage: number;

  /**
   * Visibility distance (km)
   */
  visibility: number;

  /**
   * Timestamp of measurement
   */
  timestamp: string;

  /**
   * Risk severity level (0-1, where 1 is critical)
   */
  riskLevel?: number;
}

/**
 * Complete weather grid snapshot
 *
 * Contains all grid cells for a specific time point
 */
export interface WeatherGrid {
  /**
   * Unique grid identifier
   */
  id: string;

  /**
   * Array of weather grid cells
   */
  cells: WeatherGridCell[];

  /**
   * Grid generation timestamp
   */
  generatedAt: string;

  /**
   * Grid update frequency (minutes)
   */
  updateFrequency: number;

  /**
   * Geographic bounds of grid
   */
  bounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
}

/**
 * Weather alert/warning
 *
 * Critical weather event requiring user attention
 */
export interface WeatherAlert {
  /**
   * Unique alert identifier
   */
  id: string;

  /**
   * Alert type/severity
   */
  type: 'warning' | 'alert' | 'advisory' | 'watch';

  /**
   * Alert severity level (1-5, higher = more severe)
   */
  severity: number;

  /**
   * Human-readable alert title
   */
  title: string;

  /**
   * Detailed alert description
   */
  description: string;

  /**
   * Affected geographic area (GeoJSON polygon)
   */
  area?: {
    type: 'Polygon';
    coordinates: number[][][];
  };

  /**
   * Alert validity period
   */
  validFrom: string;
  validTo: string;

  /**
   * Recommended actions
   */
  recommendations?: string[];

  /**
   * Alert status
   */
  status: 'active' | 'expired' | 'cancelled';

  /**
   * Creation timestamp
   */
  createdAt: string;

  /**
   * Last update timestamp
   */
  updatedAt: string;
}

/**
 * Rainfall heatmap data
 *
 * Aggregated rainfall data for visualization
 */
export interface RainfallHeatmapData {
  /**
   * Unique identifier
   */
  id: string;

  /**
   * Coordinate and intensity pairs
   */
  points: Array<{
    lat: number;
    lng: number;
    /**
     * Intensity (0-1 normalized, or mm/h)
     */
    intensity: number;
  }>;

  /**
   * Minimum intensity value in dataset
   */
  minIntensity: number;

  /**
   * Maximum intensity value in dataset
   */
  maxIntensity: number;

  /**
   * Data generation timestamp
   */
  timestamp: string;

  /**
   * Forecast period (if applicable)
   */
  forecastHour?: number;
}

/**
 * Weather forecast data
 *
 * Time-series weather predictions
 */
export interface WeatherForecast {
  /**
   * Unique forecast identifier
   */
  id: string;

  /**
   * Grid cell this forecast is for
   */
  gridCellId: string;

  /**
   * Forecast time periods
   */
  periods: Array<{
    /**
     * Forecast time
     */
    time: string;

    /**
     * Predicted temperature (°C)
     */
    temperature: number;

    /**
     * Predicted humidity (%)
     */
    humidity: number;

    /**
     * Predicted precipitation (mm/h)
     */
    precipitation: number;

    /**
     * Confidence level (0-1)
     */
    confidence: number;
  }>;

  /**
   * Forecast validity period
   */
  validFrom: string;
  validTo: string;

  /**
   * Model used for forecast
   */
  forecastModel?: string;
}

/**
 * Weather simulation configuration
 *
 * Parameters for real-time weather simulation
 */
export interface WeatherSimulationConfig {
  /**
   * Enable/disable simulation
   */
  enabled: boolean;

  /**
   * Grid resolution in degrees
   */
  gridResolution: number;

  /**
   * Update frequency in seconds
   */
  updateFrequency: number;

  /**
   * Simulation time multiplier (1 = real-time)
   */
  timeScale: number;

  /**
   * Temperature variation range (°C)
   */
  temperatureVariation: number;

  /**
   * Precipitation intensity factor (0-1)
   */
  precipitationIntensity: number;

  /**
   * Wind speed multiplier
   */
  windSpeedMultiplier: number;

  /**
   * Random seed for reproducibility
   */
  randomSeed?: number;
}

/**
 * Polling configuration for weather updates
 */
export interface WeatherPollingConfig {
  /**
   * Enable polling
   */
  enabled: boolean;

  /**
   * Poll interval in milliseconds
   */
  interval: number;

  /**
   * Retry attempts on failure
   */
  maxRetries: number;

  /**
   * Exponential backoff factor
   */
  backoffFactor: number;

  /**
   * Include forecast data in polls
   */
  includeForecast: boolean;

  /**
   * Include alerts in polls
   */
  includeAlerts: boolean;
}

/**
 * Weather feature state
 */
export interface WeatherState {
  /**
   * Current weather grid
   */
  grid: WeatherGrid | null;

  /**
   * Active weather alerts
   */
  alerts: WeatherAlert[];

  /**
   * Rainfall heatmap data
   */
  rainfallHeatmap: RainfallHeatmapData | null;

  /**
   * Forecasts (if enabled)
   */
  forecasts: WeatherForecast[];

  /**
   * Loading state
   */
  isLoading: boolean;

  /**
   * Error message
   */
  error: string | null;

  /**
   * Last successful update timestamp
   */
  lastUpdated: string | null;

  /**
   * Current simulation config
   */
  simulationConfig: WeatherSimulationConfig;

  /**
   * Polling configuration
   */
  pollingConfig: WeatherPollingConfig;
}


