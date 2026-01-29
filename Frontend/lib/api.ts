export const AuthAPI = {
    login: async (data: any) => {
        // Placeholder login - connects to backend /token typically
        const response = await fetch('/api/v1/auth/access-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams(data),
        });
        if (!response.ok) throw new Error('Login failed');
        return response.json();
    }
};

export const HealthAPI = {
    checkHealth: async () => {
        return { isAlive: true, isReady: true, lastCheck: new Date() };
    }
};

export const NetworkAPI = {
    getRoadNetwork: async () => {
        return {
            routes: [],
            lastUpdated: new Date().toISOString(),
            bounds: { north: 0, south: 0, east: 0, west: 0 }
        };
    },
    getRouteDetails: async (id: string) => {
        return {
            id,
            name: "Route " + id,
            segments: [],
            total_length_km: 0,
            average_risk_score: 0,
            source: "osrm" as const
        };
    }
};

export const WeatherAPI = {
    getWeatherGrid: async () => {
        return {
            cells: [],
            alerts: [],
            lastUpdated: new Date().toISOString()
        };
    }
};

export const RiskAPI = {
    startSimulation: async (regionId: string) => {
        return {
            job_id: "sim-" + regionId,
            region_id: regionId,
            status: "QUEUED" as const,
            progress: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
    },
    getSimulationStatus: async (jobId: string) => {
        return {
            job_id: jobId,
            region_id: "r1",
            status: "COMPLETED" as const,
            progress: 100,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
    },
    getSimulationResult: async (jobId: string) => {
        return {
            job_id: jobId,
            region_id: "r1",
            status: "COMPLETED" as const,
            progress: 100,
            results: {
                risk_assessment: {
                    overall_score: 0.5,
                    confidence: 0.9,
                    factors: []
                },
                recommendations: [],
                affected_routes: []
            }
        };
    }
};

export const setToken = (token: string) => {
    localStorage.setItem('token', token);
};
