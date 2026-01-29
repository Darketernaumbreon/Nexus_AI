const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const AuthAPI = {
    login: async (data: any) => {
        const formData = new URLSearchParams();
        formData.append('username', data.username);
        formData.append('password', data.password);

        const response = await fetch(`${API_URL}/iam/login/access-token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }
        return response.json();
    }
};

export const HealthAPI = {
    checkHealth: async () => {
        try {
            const response = await fetch(`${API_URL}/health/ready`);
            const data = await response.json();
            return {
                isAlive: response.ok,
                isReady: data.status === "ready",
                lastCheck: new Date()
            };
        } catch (e) {
            return { isAlive: false, isReady: false, lastCheck: new Date() };
        }
    }
};

export const NetworkAPI = {
    getRoadNetwork: async () => {
        // Mock data for visualization - Backend does not expose full network dump yet
        return {
            routes: [],
            lastUpdated: new Date().toISOString(),
            bounds: { north: 28.5, south: 12.5, east: 78.5, west: 77.0 }
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
        // Mock data for visualization
        return {
            cells: [],
            alerts: [],
            lastUpdated: new Date().toISOString()
        };
    }
};

export const RiskAPI = {
    startSimulation: async (regionId: string) => {
        const response = await fetch(`${API_URL}/operational/simulate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ region_id: regionId })
        });

        if (!response.ok) throw new Error('Simulation failed to start');
        return response.json();
    },
    getSimulationStatus: async (jobId: string) => {
        const response = await fetch(`${API_URL}/operational/jobs/${jobId}`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!response.ok) throw new Error('Failed to fetch job status');
        return response.json();
    },
    getSimulationResult: async (jobId: string) => {
        // Reuse status endpoint as it returns result on completion
        return RiskAPI.getSimulationStatus(jobId);
    }
};

export const setToken = (token: string) => {
    localStorage.setItem('token', token);
};
