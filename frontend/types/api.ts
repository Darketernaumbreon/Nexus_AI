// Generic API response types
// Foundation for type-safe API communication

export interface ApiResponse<T> {
    data: T;
    message?: string;
}

export interface ApiError {
    message: string;
    status?: number;
    data?: unknown;
}

// Health check response
export interface HealthCheckResponse {
    status: "ok" | "down";
    timestamp: string;
    version?: string;
}
