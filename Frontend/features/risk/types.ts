/**
 * Risk Simulation Feature - Type Definitions
 *
 * Core types for risk analysis, simulations, and scenario modeling
 * Supports historical data, real-time updates, and forecast integration
 */

/**
 * Risk simulation status
 */
export type SimulationStatus =
  | 'idle'
  | 'initializing'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

/**
 * Risk severity level
 */
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

/**
 * Risk factor categories
 */
export type RiskFactor =
  | 'weather'
  | 'traffic'
  | 'infrastructure'
  | 'environmental'
  | 'accident'
  | 'construction';

/**
 * Individual risk data point
 */
export interface RiskPoint {
  /**
   * Unique identifier
   */
  id: string;

  /**
   * Latitude coordinate
   */
  latitude: number;

  /**
   * Longitude coordinate
   */
  longitude: number;

  /**
   * Overall risk score (0-1, where 1 is maximum risk)
   */
  riskScore: number;

  /**
   * Risk severity level
   */
  level: RiskLevel;

  /**
   * Primary risk factor
   */
  factor: RiskFactor;

  /**
   * Contributing factors
   */
  factors: Partial<Record<RiskFactor, number>>;

  /**
   * Description of risk
   */
  description: string;

  /**
   * Timestamp
   */
  timestamp: string;

  /**
   * Confidence level (0-1)
   */
  confidence?: number;

  /**
   * Recommended actions
   */
  recommendations?: string[];
}

/**
 * Risk simulation configuration
 */
export interface RiskSimulationConfig {
  /**
   * Simulation identifier
   */
  id: string;

  /**
   * Name of simulation
   */
  name: string;

  /**
   * Description
   */
  description?: string;

  /**
   * Geographic bounds
   */
  bounds: {
    north: number;
    south: number;
    east: number;
    west: number;
  };

  /**
   * Weather conditions to simulate
   */
  weatherScenario?: 'clear' | 'rainy' | 'fog' | 'severe' | 'flood';

  /**
   * Traffic conditions
   */
  trafficScenario?: 'light' | 'moderate' | 'heavy' | 'congested';

  /**
   * Include accident scenarios
   */
  includeAccidents?: boolean;

  /**
   * Simulation duration in hours
   */
  duration: number;

  /**
   * Time step for simulation (minutes)
   */
  timeStep: number;

  /**
   * Random seed for reproducibility
   */
  randomSeed?: number;

  /**
   * Parameters for each risk factor
   */
  riskFactorWeights: Partial<Record<RiskFactor, number>>;

  /**
   * Create timestamp
   */
  createdAt: string;

  /**
   * Last modified timestamp
   */
  updatedAt: string;
}

/**
 * Risk simulation result
 */
export interface RiskSimulationResult {
  /**
   * Unique result identifier
   */
  id: string;

  /**
   * Reference to simulation config
   */
  simulationId: string;

  /**
   * Simulation status
   */
  status: SimulationStatus;

  /**
   * Risk data points generated
   */
  riskPoints: RiskPoint[];

  /**
   * Overall risk statistics
   */
  statistics: {
    /**
     * Average risk score
     */
    averageRiskScore: number;

    /**
     * Maximum risk score
     */
    maxRiskScore: number;

    /**
     * Minimum risk score
     */
    minRiskScore: number;

    /**
     * High-risk area count
     */
    highRiskAreaCount: number;

    /**
     * Critical-risk area count
     */
    criticalRiskAreaCount: number;

    /**
     * Area-weighted risk average
     */
    areaDensityRisk: number;
  };

  /**
   * Simulation progress (0-100)
   */
  progress: number;

  /**
   * Start time
   */
  startTime: string;

  /**
   * End time (if completed)
   */
  endTime?: string;

  /**
   * Duration in seconds
   */
  duration?: number;

  /**
   * Error message (if failed)
   */
  error?: string;

  /**
   * Warnings encountered
   */
  warnings?: string[];

  /**
   * Last update timestamp
   */
  updatedAt: string;
}

/**
 * Risk simulation history entry
 */
export interface RiskSimulationHistory {
  /**
   * Simulation result ID
   */
  resultId: string;

  /**
   * Simulation name
   */
  name: string;

  /**
   * Simulation configuration
   */
  config: RiskSimulationConfig;

  /**
   * Statistics from result
   */
  statistics: RiskSimulationResult['statistics'];

  /**
   * Completion status
   */
  status: SimulationStatus;

  /**
   * Duration in seconds
   */
  duration: number;

  /**
   * Execution timestamp
   */
  timestamp: string;

  /**
   * Number of risk points generated
   */
  pointCount: number;

  /**
   * Tags for organization
   */
  tags?: string[];

  /**
   * Notes/comments
   */
  notes?: string;
}

/**
 * Polling configuration for simulations
 */
export interface SimulationPollingConfig {
  /**
   * Enable polling
   */
  enabled: boolean;

  /**
   * Poll interval in milliseconds
   */
  interval: number;

  /**
   * Maximum retries on failure
   */
  maxRetries: number;

  /**
   * Exponential backoff factor
   */
  backoffFactor: number;

  /**
   * Stop polling when simulation completes
   */
  stopOnCompletion: boolean;
}

/**
 * Risk analysis state
 */
export interface RiskState {
  /**
   * Current simulation result
   */
  currentResult: RiskSimulationResult | null;

  /**
   * Simulation history
   */
  history: RiskSimulationHistory[];

  /**
   * Selected result for viewing
   */
  selectedResult: RiskSimulationResult | null;

  /**
   * Loading state
   */
  isLoading: boolean;

  /**
   * Polling state
   */
  isPolling: boolean;

  /**
   * Error message
   */
  error: string | null;

  /**
   * Last update timestamp
   */
  lastUpdated: string | null;

  /**
   * Polling configuration
   */
  pollingConfig: SimulationPollingConfig;
}


