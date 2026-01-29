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
        const response = await fetch(`${API_URL}/routing/network`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!response.ok) throw new Error('Failed to fetch road network');
        return response.json();
    },
    getRouteDetails: async (id: string) => {
        // Still mocked for detailed view pending backend support
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
        // Fetch comprehensive weather grid from backend
        // This includes both alert zones and general regional forecast
        const response = await fetch(`${API_URL}/weather/grid`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!response.ok) throw new Error('Failed to fetch weather data');
        return response.json();
    },
    getIMDRainfall: async () => {
        const response = await fetch(`${API_URL}/alerts/imd-rainfall`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        if (!response.ok) throw new Error('Failed to fetch IMD data');
        return response.json();
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
            body: JSON.stringify({ region_id: regionId, parameters: {} })
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
        return RiskAPI.getSimulationStatus(jobId);
    }
};

export const setToken = (token: string) => {
    localStorage.setItem('token', token);
};
