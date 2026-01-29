/**
 * useMapInteraction Hook
 * Manage map interaction state (zoom, center, bounds, layer visibility)
 * 
 * Syncs with URL query params for bookmarkable map states
 * 
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.2.3: State & Props)
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

import type { MapInteractionState, MapBounds, LatLng } from '../types';

/**
 * Default India bounds for reset
 */
const DEFAULT_BOUNDS: MapBounds = {
  north: 35.5,
  south: 8.0,
  east: 97.4,
  west: 68.2,
};

const DEFAULT_CENTER: LatLng = {
  lat: 20.5937,
  lng: 78.9629,
};

/**
 * useMapInteraction Hook
 *
 * Manages all map interaction state and synchronizes with URL
 *
 * **State Managed**:
 * - Zoom level (0-21)
 * - Map center (latitude, longitude)
 * - Viewport bounds (north, south, east, west)
 * - Selected route ID
 * - Layer visibility (weather, routes, traffic)
 *
 * **URL Synchronization**:
 * Query parameters for bookmarkable states:
 * - `?zoom=6`
 * - `?lat=20.5&lng=78.9`
 * - `?route=NH-06`
 * - `?weather=true&traffic=false`
 *
 * **Usage**:
 * ```tsx
 * const {
 *   zoom,
 *   setZoom,
 *   center,
 *   setCenter,
 *   selectedRouteId,
 *   selectRoute,
 *   showWeatherLayer,
 *   toggleWeatherLayer,
 *   resetMap,
 * } = useMapInteraction();
 *
 * return (
 *   <>
 *     <MapContainer zoom={zoom} center={center} onZoomChange={setZoom} />
 *     <MapControls
 *       zoom={zoom}
 *       onZoomIn={() => setZoom(z => z + 1)}
 *       showWeatherLayer={showWeatherLayer}
 *       onWeatherLayerChange={toggleWeatherLayer}
 *     />
 *   </>
 * );
 * ```
 *
 * **Connection Points**:
 * - Used by: RoadNetworkMap.tsx (parent component)
 * - Syncs: MapContainer + MapControls state
 * - Stores: URL query parameters
 */
export function useMapInteraction() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Initialize state from URL params
  const [state, setState] = useState<MapInteractionState>({
    zoom: parseInt(searchParams.get('zoom') || '6', 10),
    center: {
      lat: parseFloat(searchParams.get('lat') || String(DEFAULT_CENTER.lat)),
      lng: parseFloat(searchParams.get('lng') || String(DEFAULT_CENTER.lng)),
    },
    bounds: DEFAULT_BOUNDS,
    selectedRouteId: searchParams.get('route') || undefined,
    showWeatherLayer: searchParams.get('weather') === 'true',
    showRouteLayer: searchParams.get('routes') !== 'false',
    showTrafficLayer: searchParams.get('traffic') === 'true',
  });

  /**
   * Update URL with current state
   */
  const updateURL = useCallback((newState: Partial<MapInteractionState>) => {
    const params = new URLSearchParams(searchParams);

    if (newState.zoom !== undefined) {
      params.set('zoom', String(newState.zoom));
    }
    if (newState.center) {
      params.set('lat', String(newState.center.lat));
      params.set('lng', String(newState.center.lng));
    }
    if (newState.selectedRouteId) {
      params.set('route', newState.selectedRouteId);
    } else {
      params.delete('route');
    }
    if (newState.showWeatherLayer !== undefined) {
      params.set('weather', String(newState.showWeatherLayer));
    }
    if (newState.showRouteLayer !== undefined) {
      params.set('routes', String(newState.showRouteLayer));
    }
    if (newState.showTrafficLayer !== undefined) {
      params.set('traffic', String(newState.showTrafficLayer));
    }

    // Update URL (non-blocking)
    router.push(`?${params.toString()}`, { scroll: false } as any);
  }, [router, searchParams]);

  /**
   * Set zoom level
   */
  const setZoom = useCallback((zoom: number) => {
    const clampedZoom = Math.max(0, Math.min(21, zoom));
    setState((prev) => ({ ...prev, zoom: clampedZoom }));
    updateURL({ zoom: clampedZoom });
  }, [updateURL]);

  /**
   * Set map center
   */
  const setCenter = useCallback((center: LatLng) => {
    setState((prev) => ({ ...prev, center }));
    updateURL({ center });
  }, [updateURL]);

  /**
   * Set map bounds
   */
  const setBounds = useCallback((bounds: MapBounds) => {
    setState((prev) => ({ ...prev, bounds }));
  }, []);

  /**
   * Select route by ID
   */
  const selectRoute = useCallback((routeId: string | undefined) => {
    setState((prev) => ({ ...prev, selectedRouteId: routeId }));
    updateURL({ selectedRouteId: routeId });
  }, [updateURL]);

  /**
   * Toggle weather layer visibility
   */
  const toggleWeatherLayer = useCallback((visible?: boolean) => {
    setState((prev) => {
      const newVisible = visible !== undefined ? visible : !prev.showWeatherLayer;
      updateURL({ showWeatherLayer: newVisible });
      return { ...prev, showWeatherLayer: newVisible };
    });
  }, [updateURL]);

  /**
   * Toggle route layer visibility
   */
  const toggleRouteLayer = useCallback((visible?: boolean) => {
    setState((prev) => {
      const newVisible = visible !== undefined ? visible : !prev.showRouteLayer;
      updateURL({ showRouteLayer: newVisible });
      return { ...prev, showRouteLayer: newVisible };
    });
  }, [updateURL]);

  /**
   * Toggle traffic layer visibility
   */
  const toggleTrafficLayer = useCallback((visible?: boolean) => {
    setState((prev) => {
      const newVisible = visible !== undefined ? visible : !prev.showTrafficLayer;
      updateURL({ showTrafficLayer: newVisible });
      return { ...prev, showTrafficLayer: newVisible };
    });
  }, [updateURL]);

  /**
   * Reset map to default view
   */
  const resetMap = useCallback(() => {
    const newState: MapInteractionState = {
      zoom: 6,
      center: DEFAULT_CENTER,
      bounds: DEFAULT_BOUNDS,
      showWeatherLayer: false,
      showRouteLayer: true,
      showTrafficLayer: false,
    };
    setState(newState);
    updateURL(newState);
  }, [updateURL]);

  /**
   * Get current state as immutable object
   */
  const getState = useCallback((): MapInteractionState => state, [state]);

  return {
    // Current state
    zoom: state.zoom,
    center: state.center,
    bounds: state.bounds,
    selectedRouteId: state.selectedRouteId,
    showWeatherLayer: state.showWeatherLayer,
    showRouteLayer: state.showRouteLayer,
    showTrafficLayer: state.showTrafficLayer,

    // State setters
    setZoom,
    setCenter,
    setBounds,
    selectRoute,
    toggleWeatherLayer,
    toggleRouteLayer,
    toggleTrafficLayer,
    resetMap,

    // Utilities
    getState,
  };
}
