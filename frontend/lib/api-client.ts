import axios from "axios";

// Create Axios instance with base configuration
const apiClient = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_BASE || "/api/proxy",
    timeout: 10000, // 10 seconds
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor
apiClient.interceptors.request.use(
    (config) => {
        // Log requests in development
        if (process.env.NODE_ENV === "development") {
            console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
        }
        return config;
    },
    (error) => {
        console.error("[API Request Error]", error);
        return Promise.reject(error);
    }
);

// Response interceptor
apiClient.interceptors.response.use(
    (response) => {
        // Log responses in development
        if (process.env.NODE_ENV === "development") {
            console.log(`[API Response] ${response.config.url}`, response.data);
        }
        // Unwrap data
        return response.data;
    },
    (error) => {
        // Normalize error shape
        const normalizedError = {
            message: error.response?.data?.message || error.message || "An error occurred",
            status: error.response?.status,
            data: error.response?.data,
        };

        console.error("[API Response Error]", normalizedError);
        return Promise.reject(normalizedError);
    }
);

export default apiClient;
