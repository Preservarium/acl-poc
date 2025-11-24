# Quick Start Guide

## Prerequisites
- Node.js 18+ and npm installed
- Backend API running at http://localhost:8000

## Installation & Run

```bash
# Navigate to frontend directory
cd /workspace/main/acl-poc/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Access the app at: **http://localhost:5173**

## Login

Use these demo credentials:
- Username: `alice` or `bob`
- Password: `password`

## What You Can Do

1. **Dashboard**: View statistics and quick actions
2. **Resources**: Browse hierarchical resource tree (Site → Plan → Sensor)
3. **Permissions**: View all your permissions (direct and via groups)

## Architecture

```
Vue 3 + TypeScript
├── Pinia (State Management)
├── Vue Router (Navigation)
├── Axios (HTTP Client)
└── TailwindCSS (Styling)
```

## Key Files

- `src/main.ts` - Entry point
- `src/App.vue` - Root component
- `src/router/index.ts` - Routes and guards
- `src/stores/auth.ts` - Authentication state
- `src/api/client.ts` - API client with interceptors

## Tech Stack

- **Vue 3**: Composition API with `<script setup>`
- **TypeScript**: Full type safety
- **Vite**: Fast build tool
- **Pinia**: State management
- **Vue Router**: Routing with guards
- **Axios**: HTTP requests with interceptors
- **TailwindCSS**: Utility-first CSS

## Project Structure

```
src/
├── api/          # API client modules
├── stores/       # Pinia stores
├── components/   # Reusable components
├── views/        # Page views
├── router/       # Route configuration
└── types.ts      # TypeScript types
```

## Features Implemented

- JWT authentication with token persistence
- Protected routes with navigation guards
- Resource tree with expand/collapse
- Permission management (grant/revoke)
- My permissions view (direct + via groups)
- Loading states and error handling
- Responsive design

## Build for Production

```bash
npm run build
```

Output: `dist/` directory

## Docker Build

```bash
docker build -t acl-poc-frontend .
docker run -p 8080:80 acl-poc-frontend
```

## Troubleshooting

**Cannot connect to backend:**
- Ensure backend is running on http://localhost:8000
- Check VITE_API_URL in .env

**401 Unauthorized:**
- Token may be expired, try logging out and back in
- Clear localStorage and try again

For more details, see:
- `README.md` - Full project documentation
- `SETUP.md` - Detailed setup guide
- `IMPLEMENTATION_REPORT.md` - Complete implementation details
