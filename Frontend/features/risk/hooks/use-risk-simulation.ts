"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import type { SimulationRequest, SimulationResult, JobStatus } from "@/types";
import { RiskAPI } from "@/lib/api";

interface UseRiskSimulationReturn {
  // MANUAL: User calls this
  startSimulation: (params: SimulationRequest) => void;

  // AUTOMATED: UI reads these
  isCalculating: boolean;
  progress: number;
  estimatedTimeRemaining: number | null;
  results: SimulationResult["results"] | null;
  error: string | null;
  status: JobStatus | null;
  jobId: string | null;

  // MANUAL: User can call this to reset
  resetSimulation: () => void;
}

export function useRiskSimulation(): UseRiskSimulationReturn {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [progress, setProgress] = useState(0);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<
    number | null
  >(null);
  const [results, setResults] = useState<SimulationResult["results"] | null>(
    null
  );
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // AUTOMATED: Polling logic
  const startPolling = useCallback((currentJobId: string) => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    const poll = async () => {
      try {
        const result = await RiskAPI.getSimulationStatus(currentJobId);

        setStatus(result.status);
        setProgress(result.progress);
        setEstimatedTimeRemaining(result.eta_seconds ?? null);

        if (result.status === "COMPLETED") {
          setResults(result.results ?? null);
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        } else if (result.status === "FAILED") {
          setError(result.error ?? "Simulation failed");
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch job status"
        );
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    };

    // Initial poll
    poll();

    // Set up polling interval (2 seconds as per spec)
    pollingIntervalRef.current = setInterval(poll, 2000);
  }, []);

  // MANUAL: User triggers simulation
  const startSimulation = useCallback(
    async (params: SimulationRequest) => {
      setIsStarting(true);
      setError(null);
      setResults(null);
      setProgress(0);
      setStatus("QUEUED");

      try {
        const job = await RiskAPI.startSimulation(params.region_id);
        setJobId(job.job_id);
        setStatus(job.status);

        // Start polling for results
        startPolling(job.job_id);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to start simulation"
        );
        setStatus("FAILED");
      } finally {
        setIsStarting(false);
      }
    },
    [startPolling]
  );

  // MANUAL: User resets simulation
  const resetSimulation = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setJobId(null);
    setStatus(null);
    setProgress(0);
    setEstimatedTimeRemaining(null);
    setResults(null);
    setError(null);
    setIsStarting(false);
  }, []);

  const isCalculating =
    isStarting || status === "QUEUED" || status === "PROCESSING";

  return {
    startSimulation,
    isCalculating,
    progress,
    estimatedTimeRemaining,
    results,
    error,
    status,
    jobId,
    resetSimulation,
  };
}
