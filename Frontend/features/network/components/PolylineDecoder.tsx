'use client';

import React from 'react';
import { decodePolyline } from '@/lib/polyline-decoder';

import type { RouteSegment, DecodedPolyline } from '../types';

/**
 * Props for PolylineDecoder component
 */
export interface PolylineDecoderProps {
  /**
   * Encoded polyline string from backend
   */
  encodedPolyline: string;

  /**
   * Callback with decoded result
   */
  onDecode?: (result: DecodedPolyline) => void;

  /**
   * Callback on decode error
   */
  onError?: (error: Error) => void;

  /**
   * Route segment (optional, for reference)
   */
  segment?: RouteSegment;

  /**
   * Debug mode (log to console)
   */
  debug?: boolean;
}

/**
 * PolylineDecoder Component (Utility)
 *
 * Decodes Google Maps polyline format to coordinates
 *
 * **Pattern**: AUTOMATED decoding via algorithm
 * Uses lib/polyline-decoder.ts which implements Google's polyline algorithm
 *
 * **Algorithm**:
 * 1. Decodes compressed polyline string
 * 2. Converts delta-encoded values to lat/lng
 * 3. Returns array of [lat, lng] coordinates
 *
 * **Usage**:
 * ```tsx
 * <PolylineDecoder
 *   encodedPolyline=encodedString}
 *   segment={routeSegment}
 *   onDecode={(result) => console.log(result.coordinates)}
 *   onError={(error) => console.error(error)}
 * />
 * ```
 *
 * **Output Example**:
 * ```json
 * {
 *   "coordinates": [[20.5, 78.9], [20.6, 78.95], ...],
 *   "distanceKm": 45.2,
 *   "bounds": {
 *     "north": 20.6,
 *     "south": 20.5,
 *     "east": 79.0,
 *     "west": 78.9
 *   }
 * }
 * ```
 *
 * **Connection Points**:
 * - Library: lib/polyline-decoder.ts ✅
 * - Used by: RiskRoute.tsx (internal decoding)
 * - Could be used by: Route visualization, distance calculation
 *
 * @reference NEXUS_AI_COMPREHENSIVE_DESIGN.md (Section 5.2.1: PolylineDecoder)
 */
export const PolylineDecoder = React.memo(
  ({
    encodedPolyline,
    onDecode,
    onError,
    segment,
    debug = false,
  }: PolylineDecoderProps) => {
    React.useEffect(() => {
      if (!encodedPolyline) {
        return;
      }

      try {
        // Decode polyline
        const coordinates = decodePolyline(encodedPolyline);

        if (debug) {
          console.log('Decoded polyline:', {
            encoded: encodedPolyline,
            coordinates,
            count: coordinates.length,
            segmentId: segment?.id,
          });
        }

        // Calculate bounds
        let north = -90,
          south = 90,
          east = -180,
          west = 180;

        coordinates.forEach(([lat, lng]) => {
          north = Math.max(north, lat);
          south = Math.min(south, lat);
          east = Math.max(east, lng);
          west = Math.min(west, lng);
        });

        // Calculate distance
        let distanceKm = 0;
        for (let i = 0; i < coordinates.length - 1; i++) {
          const [lat1, lng1] = coordinates[i];
          const [lat2, lng2] = coordinates[i + 1];

          // Haversine formula
          const R = 6371; // Earth radius in km
          const dLat = ((lat2 - lat1) * Math.PI) / 180;
          const dLng = ((lng2 - lng1) * Math.PI) / 180;
          const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos((lat1 * Math.PI) / 180) *
              Math.cos((lat2 * Math.PI) / 180) *
              Math.sin(dLng / 2) *
              Math.sin(dLng / 2);
          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
          distanceKm += R * c;
        }

        const result: DecodedPolyline = {
          coordinates,
          distanceKm,
          bounds: { north, south, east, west },
        };

        onDecode?.(result);
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        if (debug) {
          console.error('Polyline decode error:', err, {
            encoded: encodedPolyline,
            segmentId: segment?.id,
          });
        }
        onError?.(err);
      }
    }, [encodedPolyline, onDecode, onError, segment, debug]);

    // This is a non-rendering utility component
    // It doesn't display anything, only processes and passes data via callbacks
    return null;
  }
);

PolylineDecoder.displayName = 'PolylineDecoder';

export default PolylineDecoder;
