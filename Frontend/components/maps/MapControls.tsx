'use client';

import React, { useCallback } from 'react';
import { ChevronUp, ChevronDown, Home, Layers } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

/**
 * Props for MapControls component
 */
export interface MapControlsProps {
  /**
   * Current zoom level (0-21)
   */
  zoom: number;

  /**
   * Callback when zoom in button clicked
   */
  onZoomIn: () => void;

  /**
   * Callback when zoom out button clicked
   */
  onZoomOut: () => void;

  /**
   * Callback when center/recenter button clicked
   */
  onCenter: () => void;

  /**
   * Whether weather layer is visible
   */
  showWeatherLayer?: boolean;

  /**
   * Callback when weather layer toggle changes
   */
  onWeatherLayerChange?: (enabled: boolean) => void;

  /**
   * Whether route layer is visible
   */
  showRouteLayer?: boolean;

  /**
   * Callback when route layer toggle changes
   */
  onRouteLayerChange?: (enabled: boolean) => void;

  /**
   * Additional className for controls container
   */
  className?: string;

  /**
   * Position of controls (top-left, top-right, bottom-left, bottom-right)
   */
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';

  /**
   * Whether controls are disabled
   */
  disabled?: boolean;
}

/**
 * NEXUS AI Map Controls
 *
 * Provides interactive controls for map navigation and layer visibility.
 * Soft UI design with accessibility features.
 *
 * **Design Pattern**: Soft UI button group with icons
 * **Library**: lucide-react for icons, @/components/ui for base components
 * **Accessibility**: Keyboard navigation, ARIA labels, tooltips
 *
 * **Features**:
 * - Zoom in/out buttons with keyboard support
 * - Center/recenter button (returns to India bounds)
 * - Weather layer toggle (IMD data overlay)
 * - Route layer toggle (road network visibility)
 * - Responsive design for mobile and desktop
 *
 * **Usage**:
 * ```tsx
 * <MapControls
 *   zoom={6}
 *   onZoomIn={handleZoomIn}
 *   onZoomOut={handleZoomOut}
 *   onCenter={handleCenter}
 *   showWeatherLayer={isWeatherEnabled}
 *   onWeatherLayerChange={setWeatherEnabled}
 * />
 * ```
 *
 * **Connection Points**:
 * - Parent: RoadNetworkMap.tsx (features/network)
 * - Sibling: MapContainer.tsx
 * - Hooks: useMapInteraction (for map state updates)
 */
export const MapControls = React.memo(
  ({
    zoom,
    onZoomIn,
    onZoomOut,
    onCenter,
    showWeatherLayer = false,
    onWeatherLayerChange,
    showRouteLayer = true,
    onRouteLayerChange,
    className = '',
    position = 'top-left',
    disabled = false,
  }: MapControlsProps) => {
    // Position classes for different layouts
    const positionClasses: Record<string, string> = {
      'top-left': 'top-4 left-4',
      'top-right': 'top-4 right-4',
      'bottom-left': 'bottom-4 left-4',
      'bottom-right': 'bottom-4 right-4',
    };

    // Handle zoom in with keyboard support (+ key)
    const handleZoomIn = useCallback(
      (e?: React.MouseEvent | KeyboardEvent) => {
        e?.preventDefault?.();
        if (zoom < 21 && !disabled) {
          onZoomIn();
        }
      },
      [zoom, onZoomIn, disabled]
    );

    // Handle zoom out with keyboard support (- key)
    const handleZoomOut = useCallback(
      (e?: React.MouseEvent | KeyboardEvent) => {
        e?.preventDefault?.();
        if (zoom > 0 && !disabled) {
          onZoomOut();
        }
      },
      [zoom, onZoomOut, disabled]
    );

    // Handle center button with keyboard support (H key for Home)
    const handleCenter = useCallback(
      (e?: React.MouseEvent | KeyboardEvent) => {
        e?.preventDefault?.();
        if (!disabled) {
          onCenter();
        }
      },
      [onCenter, disabled]
    );

    // Handle weather layer toggle
    const handleWeatherToggle = useCallback(
      (checked: boolean) => {
        if (!disabled) {
          onWeatherLayerChange?.(checked);
        }
      },
      [onWeatherLayerChange, disabled]
    );

    // Handle route layer toggle
    const handleRouteToggle = useCallback(
      (checked: boolean) => {
        if (!disabled) {
          onRouteLayerChange?.(checked);
        }
      },
      [onRouteLayerChange, disabled]
    );

    // Keyboard event handler
    React.useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
        if (disabled) return;

        switch (e.key.toUpperCase()) {
          case '+':
          case '=':
            handleZoomIn(e);
            break;
          case '-':
          case '_':
            handleZoomOut(e);
            break;
          case 'H':
            handleCenter(e);
            break;
          default:
            break;
        }
      };

      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }, [disabled, handleZoomIn, handleZoomOut, handleCenter]);

    return (
      <div
        className={`absolute ${positionClasses[position]} z-10 ${className}`}
        role="toolbar"
        aria-label="Map controls"
      >
        <TooltipProvider>
          {/* Zoom and Navigation Controls */}
          <div className="flex flex-col gap-2 bg-white rounded-lg shadow-md p-2 border border-slate-200">
            {/* Zoom In Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 hover:bg-slate-100"
                  onClick={handleZoomIn}
                  disabled={disabled || zoom >= 21}
                  aria-label="Zoom in (+ key)"
                  title="Zoom In"
                >
                  <ChevronUp className="h-4 w-4 text-slate-600" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right" className="text-xs">
                Zoom In (+)
              </TooltipContent>
            </Tooltip>

            {/* Zoom Level Display */}
            <div className="text-center text-xs font-medium text-slate-600 py-1 px-2 bg-slate-50 rounded">
              {zoom}
            </div>

            {/* Zoom Out Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 hover:bg-slate-100"
                  onClick={handleZoomOut}
                  disabled={disabled || zoom <= 0}
                  aria-label="Zoom out (- key)"
                  title="Zoom Out"
                >
                  <ChevronDown className="h-4 w-4 text-slate-600" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right" className="text-xs">
                Zoom Out (-)
              </TooltipContent>
            </Tooltip>

            {/* Divider */}
            <div className="h-px bg-slate-200 my-1" />

            {/* Center/Home Button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 hover:bg-slate-100"
                  onClick={handleCenter}
                  disabled={disabled}
                  aria-label="Center map on India (H key)"
                  title="Center on India"
                >
                  <Home className="h-4 w-4 text-slate-600" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right" className="text-xs">
                Center Map (H)
              </TooltipContent>
            </Tooltip>
          </div>

          {/* Layer Toggle Controls */}
          <div className="flex flex-col gap-3 mt-3 bg-white rounded-lg shadow-md p-3 border border-slate-200 w-max">
            {/* Weather Layer Toggle */}
            <div className="flex items-center gap-2 cursor-pointer group">
              <Checkbox
                id="weather-layer"
                checked={showWeatherLayer}
                onCheckedChange={handleWeatherToggle}
                disabled={disabled}
                className="h-4 w-4"
              />
              <Label
                htmlFor="weather-layer"
                className="text-sm cursor-pointer select-none group-hover:text-blue-600 transition-colors"
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="flex items-center gap-1">
                      <span>📊 Weather</span>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent side="left" className="text-xs">
                    Show IMD rainfall data overlay
                  </TooltipContent>
                </Tooltip>
              </Label>
            </div>

            {/* Route Layer Toggle */}
            <div className="flex items-center gap-2 cursor-pointer group">
              <Checkbox
                id="route-layer"
                checked={showRouteLayer}
                onCheckedChange={handleRouteToggle}
                disabled={disabled}
                className="h-4 w-4"
              />
              <Label
                htmlFor="route-layer"
                className="text-sm cursor-pointer select-none group-hover:text-emerald-600 transition-colors"
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="flex items-center gap-1">
                      <span>🛣️ Routes</span>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent side="left" className="text-xs">
                    Show road network with risk colors
                  </TooltipContent>
                </Tooltip>
              </Label>
            </div>
          </div>
        </TooltipProvider>
      </div>
    );
  }
);

MapControls.displayName = 'MapControls';

export default MapControls;
