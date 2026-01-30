import { useQuery } from "@tanstack/react-query";

const OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast";
const DEFAULT_LAT = 26.1445; // Guwahati
const DEFAULT_LON = 91.7362;

interface WeatherResponse {
    current: {
        time: string;
        interval: number;
        precipitation: number;
        rain: number;
    };
    daily: {
        time: string[];
        precipitation_sum: number[];
    };
}

export function useWeather() {
    return useQuery<WeatherResponse | null>({
        queryKey: ["weather", DEFAULT_LAT, DEFAULT_LON],
        queryFn: async () => {
            try {
                const url = `${OPEN_METEO_URL}?latitude=${DEFAULT_LAT}&longitude=${DEFAULT_LON}&current=precipitation,rain&daily=precipitation_sum&timezone=auto&forecast_days=3`;
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error("Weather fetch failed");
                }
                return response.json();
            } catch (error) {
                console.error("Failed to fetch weather:", error);
                return null;
            }
        },
        staleTime: 30 * 60 * 1000, // 30 minutes
        retry: false,
    });
}
