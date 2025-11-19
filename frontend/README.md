# Frontend - Next.js Application

The frontend is a modern React application built with Next.js 14, TypeScript, and Tailwind CSS.

## Structure

```
frontend/
├── src/
│   ├── app/              # Next.js 14 app directory
│   │   ├── layout.tsx   # Root layout
│   │   ├── page.tsx     # Home page
│   │   └── globals.css  # Global styles
│   └── lib/             # Utilities
│       └── api.ts       # API client with interceptors
├── public/              # Static assets
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── tailwind.config.js   # Tailwind CSS config
├── next.config.js       # Next.js config
└── Dockerfile          # Docker configuration
```

## Setup

### Local Development

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

4. **Open browser**
   Navigate to http://localhost:3000

### Docker Development

```bash
docker build -t elk-frontend .
docker run -p 3000:3000 elk-frontend
```

## Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Type checking
npm run type-check
```

## Features

### Authentication
- JWT-based authentication
- Automatic token refresh
- Protected routes

### API Client
The `src/lib/api.ts` file provides a configured Axios instance with:
- Automatic JWT token attachment
- Token refresh on 401 errors
- Request/response interceptors

### Styling
- Tailwind CSS for utility-first styling
- Responsive design
- Custom color scheme

## Pages Structure

```
/                  # Home page
/login            # Login page
/dashboard        # Main dashboard
/logs             # Log search and viewing
/dashboards       # Dashboard management
/alerts           # Alert configuration
/settings         # User settings
```

## Components (To Be Created)

```
src/
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Footer.tsx
│   ├── logs/
│   │   ├── LogTable.tsx
│   │   ├── LogSearch.tsx
│   │   └── LogDetails.tsx
│   ├── dashboards/
│   │   ├── DashboardGrid.tsx
│   │   ├── Widget.tsx
│   │   └── ChartComponents.tsx
│   └── common/
│       ├── Button.tsx
│       ├── Input.tsx
│       └── Modal.tsx
```

## State Management

Consider adding:
- **Zustand** for global state (included in dependencies)
- **React Query** for server state (@tanstack/react-query included)

Example Zustand store:

```typescript
// src/store/auth.ts
import { create } from 'zustand'

interface AuthState {
  user: User | null
  setUser: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  logout: () => set({ user: null }),
}))
```

## Environment Variables

Create `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Building for Production

```bash
# Build
npm run build

# Start production server
npm start
```

## Deployment

### Vercel (Recommended for Next.js)
```bash
npm install -g vercel
vercel
```

### Docker
```bash
docker build -t elk-frontend .
docker run -p 3000:3000 elk-frontend
```

## Performance Optimization

- Image optimization with Next.js Image component
- Code splitting with dynamic imports
- Server-side rendering for initial load
- Static generation where possible

## TypeScript

The project uses strict TypeScript configuration. Ensure all components are properly typed.

## Testing (To Be Added)

```bash
# Install testing dependencies
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# Run tests
npm test
```
