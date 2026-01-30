// System status types

export type SystemStatus = "ONLINE" | "OFFLINE" | "DEGRADED";

export interface SystemHealthData {
    status: SystemStatus;
    latencyMs?: number;
    lastChecked: Date;
}
