'use client';

import React, { useEffect, useRef } from 'react';
import { useMap } from '@vis.gl/react-google-maps';
import { decodePolyline } from '@/lib/polyline-decoder';

import type { RouteSegment } from '../types';

/**
 * Props for RiskRoute component
 */
export interface RiskRouteProps {
  /**
   * Route segments with encoded polylines
   */
  segments: RouteSegment[];

  /**
   * Callback when route segment is clicked
   */
  onSegmentClick?: (segment: RouteSegment) => void;

  /**
   * Custom risk color mapping (optional)
   */
  riskColors?: {
    low: string; // 0-33 (Soft Emerald)
    medium: string; // 34-66 (Soft Amber)
    high: string; // 67-99 (Soft Orange)
    critical: string; // 100 (Soft Red)
  };

  /**
   * Polyline opacity (0-1)
   */
  opacity?: number;

  /**
   * Polyline weight in pixels
   */
  weight?: number;

  /**
   * Whether polylines are clickable
   */
  clickable?: boolean;

  /**
   * Highlight color for selected segment
   */
  highlightColor?: string;

  /**
   * Selected segment ID
   */
  selectedSegmentId?: string;
}

/**
 * RiskRoute Component
 *
 * Renders polylines on Google Maps with risk-based colors
 *
 * **Data Flow**:
 * 1. Receives RouteSegment[] with encoded polylines
 * 2. Decodes polylines using lib/polyline-decoder.ts ✅
 * 3. Maps risk_score to color (gradient)
 * 4. Creates google.maps.Polyline for each segment
 * 5. Renders directly to Google Maps canvas (no JSX)
 * 6. Cleans up on unmount
 *
 * **Risk Color Mapping**:
 * - 0-33: Soft Emerald (Low risk)
 * - 34-66: Soft Amber (Medium risk)
 * - 67-99: Soft Orange (High risk)
 * - 100: Soft Red (Critical)
 *
 * **Pattern**: AUTOMATED rendering via useEffect + useMap hook
 *
 * **Usage**:
 * ```tsx
 * <MapContainer zoom={6} center={{ lat: 20.5937, lng: 78.9629 }}>
 *   <RiskRoute
 *     segments={routeData.segments}
 *     onSegmentClick={handleSegmentClick}
 *     selectedSegmentId={selectedId}
 *   />
 * </MapContainer>
 * ```
 *
 * **Connection Points**:
 * - Parent: MapContainer (via children)
 * - Data from: useRouteDetails hook
 * - Library: @vis.gl/react-google-maps (useMap)
 * - Decoder: lib/polyline-decoder.ts ✅
 * - Parent: RoadNetworkMap.tsx (Phase 5)
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.2.2: RiskRoute Component)
 */
export const RiskRoute = React.memo(
  ({
    segments,
    onSegmentClick,
    riskColors = {
      low: '#34d399', // Soft Emerald
      medium: '#fbbf24', // Soft Amber
      high: '#fb923c', // Soft Orange
      critical: '#f87171', // Soft Red
    },
    opacity = 0.8,
    weight = 6,
    clickable = true,
    highlightColor = '#3b82f6',
    selectedSegmentId,
  }: RiskRouteProps) => {
    const map = useMap();
    const polylinesRef = useRef<google.maps.Polyline[]>([]);
    const clickListenersRef = useRef<google.maps.MapsEventListener[]>([]);

    useEffect(() => {
      if (!map || !segments.length) return;

      // Cleanup previous polylines
      polylinesRef.current.forEach((polyline) => polyline.setMap(null));
      clickListenersRef.current.forEach((listener) =>
        google.maps.event.removeListener(listener)
      );
      polylinesRef.current = [];
      clickListenersRef.current = [];

      // Create polylines for each segment
      segments.forEach((segment) => {
        try {
          // Decode polyline
          const coordinates = decodePolyline(segment.encodedPolyline);

          // Determine color based on risk score
          let color = riskColors.low;
          if (segment.risk_score > 100) {
            color = riskColors.critical;
          } else if (segment.risk_score > 67) {
            color = riskColors.high;
          } else if (segment.risk_score > 33) {
            color = riskColors.medium;
          }

          // Use highlight color if selected
          const isSelected = segment.id === selectedSegmentId;
          if (isSelected) {
            color = highlightColor;
          }

          // Create polyline
          const polyline = new google.maps.Polyline({
            path: coordinates.map((coord) => ({
              lat: coord[0],
              lng: coord[1],
            })),
            strokeColor: color,
            strokeOpacity: isSelected ? 1 : opacity,
            strokeWeight: isSelected ? weight + 2 : weight,
            map: map,
            clickable: clickable,
            geodesic: true,
          });

          // Add click listener
          if (clickable && onSegmentClick) {
            const listener = polyline.addListener('click', () => {
              onSegmentClick(segment);
            });
            clickListenersRef.current.push(listener);
          }

          // Add hover effect
          if (clickable) {
            polyline.addListener('mouseover', () => {
              polyline.setOptions({
                strokeOpacity: 1,
                strokeWeight: weight + 1,
              });
            });

            polyline.addListener('mouseout', () => {
              if (!isSelected) {
                polyline.setOptions({
                  strokeOpacity: opacity,
                  strokeWeight: weight,
                });
              }
            });
          }

          polylinesRef.current.push(polyline);
        } catch (error) {
          console.error(`Failed to decode polyline for segment ${segment.id}:`, error);
        }
      });

      // Cleanup on unmount
      return () => {
        polylinesRef.current.forEach((polyline) => polyline.setMap(null));
        clickListenersRef.current.forEach((listener) =>
          google.maps.event.removeListener(listener)
        );
      };
    }, [map, segments, riskColors, opacity, weight, clickable, highlightColor, selectedSegmentId, onSegmentClick]);

    // Renders directly to Google Maps canvas, returns nothing to JSX
    return null;
  }
);

RiskRoute.displayName = 'RiskRoute';

export default RiskRoute;
