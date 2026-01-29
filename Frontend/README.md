# NEXUS AI Frontend

**Next.js-based frontend for NEXUS AI** - A comprehensive road network risk assessment and weather simulation platform.

## Project Structure

This is a **Next.js 16** project with TypeScript, using App Router architecture. The project structure differs from traditional Vite/React setups mentioned in design documents.

```
Frontend/
├── app/                          # Next.js App Router (replaces src/ for routing)
│   ├── layout.tsx               # Root layout wrapper
│   ├── page.tsx                 # Home page
│   ├── globals.css              # Global styles
│   ├── login/                   # Login feature
│   ├── network/                 # Network visualization feature
│   ├── risk/                    # Risk simulation feature
│   └── weather/                 # Weather simulation feature
│
├── components/                   # Reusable UI components
│   ├── ui/                      # Shadcn/ui base components (45+ components)
│   ├── layout/                  # Layout components (header, sidebar, etc.)
│   ├── feedback/                # Feedback components (loaders, alerts, etc.)
│   └── theme-provider.tsx       # Theme context provider
│
├── features/                     # Feature-specific modules
│   ├── auth/                    # Authentication module
│   ├── network/                 # Road network module
│   │   ├── api.ts              # Network API functions
│   │   ├── types.ts            # Type definitions
│   │   ├── hooks/              # Custom hooks
│   │   └── components/         # Feature components
│   ├── risk/                    # Risk simulation module
│   │   ├── api.ts              # Risk API functions
│   │   ├── types.ts            # Type definitions
│   │   ├── constants.ts        # Configuration constants
│   │   ├── hooks/              # Custom hooks
│   │   └── components/         # Feature components
│   └── weather/                 # Weather simulation module
│       ├── api.ts              # Weather API functions
│       ├── types.ts            # Type definitions
│       ├── hooks/              # Custom hooks
│       └── components/         # Feature components
│
├── hooks/                        # Global custom hooks
│   ├── use-health-check.ts     # API health check
│   ├── use-mobile.ts           # Responsive design
│   ├── use-queries.ts          # React Query utilities
│   └── use-toast.ts            # Toast notifications
│
├── lib/                          # Utility libraries
│   ├── api.ts                  # API client configuration
│   ├── auth-context.tsx        # Authentication context
│   ├── query-client.tsx        # React Query setup
│   ├── utils.ts                # Helper functions
│   └── validations.ts          # Form validations
│
├── types/                        # Global TypeScript types
│   └── index.ts                # Shared type definitions
│
├── styles/                       # Global styles
│   ├── globals.css             # Global CSS
│   └── animations.css          # Custom animations
│
├── public/                       # Static assets
│
├── Configuration Files
├── next.config.mjs             # Next.js configuration
├── tsconfig.json               # TypeScript configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── postcss.config.mjs          # PostCSS configuration
├── components.json             # Shadcn/ui configuration
├── package.json                # Dependencies
├── .env.local                  # Environment variables
└── .gitignore                  # Git ignore rules
```

## Key Architecture Differences

### Next.js vs Vite/React Design

The design document mentions `/src/` folder structure typical of Vite projects, but this implementation uses **Next.js 16** with the **App Router**:

| Aspect | Design Document | Implementation |
|--------|-----------------|-----------------|
| **Build Tool** | Vite | Next.js |
| **Routing** | React Router | Next.js App Router (`/app` folder) |
| **Entry Point** | `src/main.tsx` | `app/layout.tsx` + `app/page.tsx` |
| **Type Defs** | `vite-env.d.ts` | `next-env.d.ts` |
| **Package** | N/A | `next.config.mjs` |

## Running the Project

### Development Server

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Server runs at http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Linting

```bash
npm run lint
```

## Environment Configuration

Configuration is managed via `.env.local` with the following sections:

- **API Configuration**: Backend URL, timeouts, API keys
- **Authentication**: Session management, OAuth providers
- **Feature Flags**: Enable/disable features (network, weather, risk)
- **UI Configuration**: Theme, map provider, defaults
- **Logging & Debugging**: Debug levels, verbose logging
- **Data & Caching**: Cache durations, local storage settings
- **Monitoring**: Analytics and error tracking (Sentry)
- **Development**: Port, error details, dev tools

See `.env.local` for complete configuration options.

## Technology Stack

### Core
- **Next.js 16** - React framework with built-in routing
- **TypeScript** - Type safety
- **React 18** - UI library
- **TailwindCSS** - Utility-first CSS framework

### UI & Components
- **Shadcn/ui** - High-quality React components (45+)
- **Radix UI** - Headless component library
- **Lucide React** - Icon library
- **Sonner** - Toast notifications
- **Recharts** - Data visualization

### State Management & Data Fetching
- **React Query** - Server state management and caching
- **React Hook Form** - Form handling
- **Zod** - Schema validation

### Development
- **ESLint** - Code linting
- **PostCSS** - CSS processing
- **tailwindcss-animate** - Tailwind animation utilities

## Feature Modules

### 1. **Network Feature** (`features/network/`)
Road network visualization and routing

**Files:**
- `api.ts` - Route fetching with fallback support
- `types.ts` - Type definitions for routes, nodes, networks
- `hooks/useRoadNetwork.ts` - Network data management
- `hooks/useRouteDetails.ts` - Route-specific data
- `hooks/useMapInteraction.ts` - Map interaction handling
- **Components**: Network map, route list, node details, offline banner, polyline decoder, risk routes

**Key Capabilities:**
- Primary/fallback data sources (PostGIS, local backup, cache)
- Real-time route updates via WebSocket
- Offline fallback system
- Risk-aware routing

---

### 2. **Weather Feature** (`features/weather/`)
Weather simulation and real-time monitoring

**Files:**
- `api.ts` - Weather grid, alert, and forecast APIs
- `types.ts` - Weather grid, alert, forecast, simulation types
- `hooks/useWeatherGrid.ts` - Grid data with fallback
- `hooks/useAlerts.ts` - Alert management
- `hooks/useWeatherPolling.ts` - Intelligent polling with backoff
- **Components**: Grid visualization, alert banner, rainfall heatmap, weather charts

**Key Capabilities:**
- Real-time weather grid visualization
- Active alert management with severity filtering
- Rainfall intensity heatmap
- Multi-metric forecast charts (temperature, precipitation, humidity)
- WebSocket real-time updates
- Exponential backoff on failures

---

### 3. **Risk Feature** (`features/risk/`)
Risk simulation and scenario analysis

**Files:**
- `api.ts` - Simulation creation, polling, WebSocket streaming
- `types.ts` - Simulation configs, results, history
- `constants.ts` - Risk levels, colors, scenarios, endpoints
- `hooks/useSimulationStatus.ts` - Lightweight status polling
- `hooks/useSimulationPoll.ts` - Full result polling with fallback
- **Components**: Simulation history, skeleton loaders, status indicators, results viewer

**Key Capabilities:**
- Risk scenario simulation with weather and traffic factors
- Lightweight status endpoint for progress tracking
- Full result polling with automatic fallback
- Simulation history with filtering and export
- Real-time WebSocket updates
- Comprehensive error handling

---

### 4. **Authentication Feature** (`features/auth/`)
User authentication and session management

**Components:**
- `LoginForm.tsx` - Credential-based login
- `LogoutButton.tsx` - Session termination
- `SessionGuard.tsx` - Route protection

---

## Animations & Transitions

Custom animations defined in `styles/animations.css`:

- **Fade**: `fade-in`, `fade-out`
- **Slide**: `slide-in-up`, `slide-in-down`, `slide-in-left`, `slide-in-right`
- **Scale**: `scale-in`, `scale-out`
- **Pulse**: `pulse-soft`, `pulse-strong`
- **Shimmer**: Loading skeletons
- **Bounce**: Subtle UI movements
- **Status**: Active, warning, error indicators
- **Toast**: Notification animations

All respect `prefers-reduced-motion` for accessibility.

## Global Styling

### Typography & Colors
- Defined via CSS custom properties (HSL format)
- Dark mode support via class selector
- Configured in component styles

### Layout Components
- **AppLayout**: Main application wrapper
- **Header**: Navigation and user info
- **Sidebar**: Feature navigation
- **StatusBar**: System status indicator

## API Integration

### Client Configuration (`lib/api.ts`)
- Base URL from `NEXT_PUBLIC_API_BASE_URL`
- Request/response interceptors
- Error handling with `handleApiError()`
- Type-safe fetch wrappers

### Feature APIs
Each feature implements:
- **Primary endpoint** - Real-time data
- **Fallback endpoints** - Offline/degraded mode
- **Cache layer** - Local storage
- **WebSocket** - Real-time updates

## Build Output

Production build generates:
- Static pages for: `/`, `/login`, `/network`, `/risk`, `/weather`
- Optimized JavaScript bundles
- Tree-shaken dependencies
- CSS minification via Tailwind

View build status: Check `.next/` directory

## Type Safety

All modules are fully typed with TypeScript:

```typescript
// Example: Type-safe feature module
import type { WeatherGrid, WeatherAlert } from '@/features/weather/types';
import { fetchWeatherGrid } from '@/features/weather/api';

const grid: WeatherGrid = await fetchWeatherGrid();
```

## Authentication Flow

1. User navigates to `/login`
2. `LoginForm` submits credentials
3. `auth-context` manages session
4. `SessionGuard` protects routes
5. `LogoutButton` terminates session

## State Management

### React Query
- Server state (API data)
- Automatic caching and invalidation
- Background refetching

### Context API
- Authentication state
- Theme configuration
- Query client instance

### Local State
- Component-level state via `useState`
- Form state via React Hook Form

## Error Handling

### API Layer
```typescript
try {
  const data = await fetchData();
} catch (error) {
  if (error instanceof Error) {
    handleError(error.message);
  }
}
```

### Fallback Strategies
1. Try primary endpoint
2. Use cached data on error
3. Display offline message
4. Retry with exponential backoff

## Performance Optimizations

- **Code Splitting**: Route-based chunking
- **Image Optimization**: Next.js Image component
- **CSS Minification**: Tailwind production builds
- **Type Checking**: Strict TypeScript config
- **Caching**: Aggressive cache strategies

## Development Guidelines

### Creating New Features

1. Create feature folder: `features/[feature-name]/`
2. Define types: `features/[feature-name]/types.ts`
3. Create API: `features/[feature-name]/api.ts`
4. Add hooks: `features/[feature-name]/hooks/`
5. Build components: `features/[feature-name]/components/`
6. Create page: `app/[feature-name]/page.tsx`

### Component Structure

```typescript
// Feature component template
import type { ComponentProps } from './types';

export const MyComponent = ({ prop1, prop2 }: ComponentProps) => {
  return <div>{/* JSX */}</div>;
};

MyComponent.displayName = 'MyComponent';
export default MyComponent;
```

## Troubleshooting

### Build Failures
- Clear `.next/` directory: `rm -rf .next`
- Rebuild: `npm run build`

### Runtime Errors
- Check `.env.local` configuration
- Verify API backend is running
- Check browser console for errors

### Type Errors
- Run `tsc --noEmit` to check types
- Ensure TypeScript version compatibility

## Contributing

Follow the architecture patterns established in this project:

1. **Feature-first organization**: Group related code
2. **Type safety**: Use TypeScript throughout
3. **Error handling**: Implement fallbacks and retries
4. **Testing**: Add tests for critical paths
5. **Documentation**: Comment complex logic

## Related Documentation

- [NEXUS AI Comprehensive Design](../NEXUS_AI_COMPREHENSIVE_DESIGN.md)
- [Next.js Documentation](https://nextjs.org)
- [TypeScript Handbook](https://www.typescriptlang.org/docs)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [React Query Docs](https://tanstack.com/query/latest)
- [Shadcn/ui Docs](https://ui.shadcn.com)

---

**Last Updated**: January 28, 2026  
**Project Version**: 0.1.0  
**Next.js Version**: 16.0.10
