'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { APIProvider, Map } from '@vis.gl/react-google-maps';

/**
 * Map bounds interface for viewport control
 */
interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

/**
 * Map center coordinates
 */
interface MapCenter {
  lat: number;
  lng: number;
}

/**
 * Props for MapContainer component
 */
export interface MapContainerProps {
  /**
   * Initial map bounds (defines viewport)
   * If not provided, defaults to India bounds
   */
  bounds?: MapBounds;

  /**
   * Initial map center coordinates
   * Default: India center (lat: 20.5937, lng: 78.9629)
   */
  center?: MapCenter;

  /**
   * Initial zoom level (0-21)
   * Default: 6 (country-level view)
   */
  zoom?: number;

  /**
   * Callback when map bounds change (user pan/zoom)
   */
  onBoundsChange?: (bounds: MapBounds) => void;

  /**
   * Callback when zoom level changes
   */
  onZoomChange?: (zoom: number) => void;

  /**
   * Callback when map center changes
   */
  onCenterChange?: (center: MapCenter) => void;

  /**
   * Child components (markers, polylines, etc.)
   */
  children?: React.ReactNode;

  /**
   * Whether to show weather layer (controlled by parent)
   */
  showWeatherLayer?: boolean;

  /**
   * Additional className for map container
   */
  className?: string;

  /**
   * API key for Google Maps
   * Default: reads from NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
   */
  apiKey?: string;
}

/**
 * NEXUS AI Map Container
 *
 * Wraps Google Maps API with React integration and memoization.
 * Provides a controlled interface for map state management.
 *
 * **Design Pattern**: Soft UI styling with India-focused bounds
 * **Library**: @vis.gl/react-google-maps (GoogleMap wrapper)
 * **Performance**: React.memo to prevent unnecessary re-renders
 *
 * **Usage**:
 * ```tsx
 * <MapContainer
 *   bounds={userBounds}
 *   onBoundsChange={handleBoundsChange}
 *   showWeatherLayer={isWeatherEnabled}
 * >
 *   <RiskRoute segments={routeData} />
 *   <RainfallHeatmap weather={weatherData} />
 * </MapContainer>
 * ```
 *
 * **Connection Points**:
 * - Parent: RoadNetworkMap.tsx (features/network)
 * - Children: RiskRoute.tsx, RainfallHeatmap.tsx
 * - Hooks: useMapInteraction (for user pan/zoom)
 * - Library: polyline-decoder.ts (for route visualization)
 */
export const MapContainer = React.memo(
  ({
    bounds,
    center,
    zoom = 6,
    onBoundsChange,
    onZoomChange,
    onCenterChange,
    children,
    showWeatherLayer,
    className = '',
    apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY,
  }: MapContainerProps) => {
    // Default India bounds
    const DEFAULT_CENTER: MapCenter = { lat: 20.5937, lng: 78.9629 };
    const DEFAULT_BOUNDS: MapBounds = {
      north: 35.5,
      south: 8.0,
      east: 97.4,
      west: 68.2,
    };

    // State management
    const [mapZoom, setMapZoom] = useState(zoom);
    const [mapCenter, setMapCenter] = useState(center || DEFAULT_CENTER);

    // Handle zoom changes
    const handleZoomChange = useCallback(
      (newZoom: number) => {
        setMapZoom(newZoom);
        onZoomChange?.(newZoom);
      },
      [onZoomChange]
    );

    // Handle center changes
    const handleCenterChange = useCallback(
      (newCenter: MapCenter) => {
        setMapCenter(newCenter);
        onCenterChange?.(newCenter);
      },
      [onCenterChange]
    );

    // Handle bounds changes (from map interaction)
    const handleBoundsChange = useCallback(() => {
      // Note: Actual bounds calculation happens in parent via useMapInteraction
      // This callback is triggered when user pans/zooms
      if (onBoundsChange) {
        // Parent will get updated bounds from map event
        onBoundsChange(bounds || DEFAULT_BOUNDS);
      }
    }, [bounds, onBoundsChange]);

    // Memoize map props to prevent unnecessary re-renders
    const mapProps = useMemo(
      () => ({
        zoom: mapZoom,
        center: mapCenter,
        mapId: 'nexus-ai-map', // Custom map styling ID
        disableDefaultUI: false,
        zoomControl: false, // We provide custom controls via MapControls
        fullscreenControl: false,
        streetViewControl: false,
        mapTypeControl: false,
        // Restrict map bounds to India region
        restriction: {
          latLngBounds: {
            north: DEFAULT_BOUNDS.north,
            south: DEFAULT_BOUNDS.south,
            east: DEFAULT_BOUNDS.east,
            west: DEFAULT_BOUNDS.west,
          },
          strictBounds: false,
        },
      }),
      [mapZoom, mapCenter]
    );

    // Validate API key
    if (!apiKey) {
      return (
        <div className={`w-full h-full flex items-center justify-center bg-slate-50 ${className}`}>
          <div className="text-center p-4">
            <p className="text-sm font-medium text-slate-700">
              Map Configuration Error
            </p>
            <p className="text-xs text-slate-500 mt-1">
              NEXT_PUBLIC_GOOGLE_MAPS_API_KEY not configured
            </p>
          </div>
        </div>
      );
    }

    return (
      <APIProvider apiKey={apiKey}>
        <div className={`w-full h-full relative ${className}`}>
          {/* Main Map Component */}
          <Map
            {...mapProps}
            onZoomChanged={(zoom) => handleZoomChange(zoom.detail.zoom)}
            onCenterChanged={(event) => {
              if (event.detail?.center) {
                handleCenterChange(event.detail.center);
              }
              handleBoundsChange();
            }}
            gestureHandling="greedy"
            tilt={0}
          >
            {/* Child components: RiskRoute, RainfallHeatmap, etc. */}
            {children}
          </Map>

          {/* Weather layer indicator (shown when enabled) */}
          {showWeatherLayer && (
            <div className="absolute bottom-4 left-4 text-xs bg-blue-50 border border-blue-200 rounded px-2 py-1 text-blue-700">
              📊 Weather Layer Active
            </div>
          )}
        </div>
      </APIProvider>
    );
  }
);

MapContainer.displayName = 'MapContainer';

export default MapContainer;
