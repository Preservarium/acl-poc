# Frontend Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd /workspace/main/acl-poc/frontend
npm install
```

### 2. Configure Environment

```bash
# Create .env file
cp .env.example .env

# Edit .env if needed (default: VITE_API_URL=/api)
```

### 3. Start Development Server

```bash
npm run dev
```

The app will be available at http://localhost:5173

## Development

### Available Scripts

- `npm run dev` - Start development server with HMR
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Lint and fix code

### Project Structure

```
src/
├── api/              # API client with axios
│   ├── client.ts     # Base axios instance with interceptors
│   ├── auth.ts       # Authentication endpoints
│   ├── permissions.ts # Permission management
│   ├── resources.ts  # Resource CRUD
│   └── users.ts      # User management
│
├── stores/           # Pinia state management
│   ├── auth.ts       # Authentication state
│   ├── permissions.ts # Permission state
│   └── resources.ts  # Resource state
│
├── components/       # Reusable Vue components
│   ├── AppLayout.vue      # Main app layout
│   ├── LoginForm.vue      # Login form
│   ├── ResourceTree.vue   # Hierarchical resource tree
│   ├── PermissionList.vue # Permission display
│   └── PermissionGrant.vue # Permission granting
│
├── views/            # Page components
│   ├── LoginView.vue      # Login page
│   ├── DashboardView.vue  # Dashboard
│   ├── ResourcesView.vue  # Resource management
│   └── PermissionsView.vue # User permissions
│
├── router/           # Vue Router
│   └── index.ts      # Route configuration
│
├── types.ts          # TypeScript types
├── main.ts           # App entry point
└── App.vue           # Root component
```

## Authentication Flow

1. User submits login form with username/password
2. LoginForm calls `authStore.login(credentials)`
3. Auth store sends POST to `/auth/login` via authAPI
4. Backend returns JWT token
5. Token stored in localStorage
6. Auth store fetches current user via `/auth/me`
7. Router guard redirects to dashboard

### Protected Routes

All routes except `/login` require authentication. The router guard:
- Checks if user is authenticated
- Redirects to login if not
- Stores redirect URL for post-login navigation

### Token Management

- Token stored in localStorage as `access_token`
- Axios interceptor adds `Authorization: Bearer {token}` to all requests
- 401 responses trigger automatic logout and redirect to login

## API Integration

### Axios Client Configuration

```typescript
// Base URL from environment or defaults to /api
baseURL: '/api'

// Request interceptor adds JWT token
headers: { Authorization: `Bearer ${token}` }

// Response interceptor handles errors
401 → Clear token, redirect to login
```

### API Modules

Each API module exports typed functions:

```typescript
// Example: auth.ts
export const authAPI = {
  login(credentials: LoginRequest): Promise<LoginResponse>
  getCurrentUser(): Promise<User>
  logout(): void
}
```

## State Management

### Pinia Stores

**Auth Store** (`stores/auth.ts`)
- State: user, token, loading, error
- Getters: isAuthenticated, username
- Actions: login(), logout(), fetchCurrentUser(), initialize()

**Resources Store** (`stores/resources.ts`)
- State: resources, selectedResource, loading, error
- Getters: resourceTree, rootResources
- Actions: fetchResources(), createResource(), updateResource(), deleteResource()

**Permissions Store** (`stores/permissions.ts`)
- State: resourcePermissions (Map), myPermissions, loading, error
- Actions: grantPermission(), revokePermission(), fetchResourcePermissions()

## Styling

### TailwindCSS

The project uses TailwindCSS utility classes for styling. Custom utility classes defined in `style.css`:

- `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger` - Button styles
- `.input` - Form input styling
- `.label` - Form label styling
- `.card`, `.card-header` - Card components
- `.spinner` - Loading spinner animation

### Color Scheme

- Primary: Blue (primary-50 to primary-900)
- Background: Gray-50
- Text: Gray-900

## Components

### AppLayout

Main layout wrapper with:
- Top navigation bar
- Route links (Dashboard, Resources, Permissions)
- User menu with username and logout
- Slot for page content

### LoginForm

- Username and password inputs
- Form validation
- Loading state
- Error display
- Demo user hint

### ResourceTree

Hierarchical tree display with:
- Expand/collapse functionality
- Icons for resource types
- Action buttons (edit, manage permissions)

### PermissionList

Display permissions table with:
- User/group grantee
- Permission level
- Inherit flag
- Revoke action

### PermissionGrant

Form to grant new permissions:
- Grantee type selector (user/group)
- Grantee dropdown
- Permission level selector
- Inherit checkbox

## Testing Locally

### 1. Ensure Backend is Running

The frontend expects the backend API at http://localhost:8000 (or VITE_API_URL).

```bash
# In another terminal, start the backend
cd /workspace/main/acl-poc/backend
python -m uvicorn app.main:app --reload
```

### 2. Start Frontend

```bash
npm run dev
```

### 3. Test Login

Navigate to http://localhost:5173 and login with:
- Username: `alice` or `bob`
- Password: `password`

## Production Build

### Build

```bash
npm run build
```

Output: `dist/` directory with optimized static files

### Preview Build

```bash
npm run preview
```

### Docker Build

```bash
# Build image
docker build -t acl-poc-frontend .

# Run container
docker run -p 8080:80 acl-poc-frontend
```

The Dockerfile uses multi-stage build:
1. Build stage: Install deps, build Vue app
2. Production stage: Serve with nginx

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: `/api`)

## Troubleshooting

### Cannot connect to backend

Check:
1. Backend is running on http://localhost:8000
2. VITE_API_URL is set correctly
3. CORS is enabled in backend

### 401 Unauthorized errors

Check:
1. Token is present in localStorage
2. Token is not expired
3. Authorization header is being sent

### Type errors

Run:
```bash
npm run build
```

TypeScript will show all type errors.

## Browser DevTools

### Vue DevTools

Install Vue DevTools browser extension to:
- Inspect component tree
- View Pinia store state
- Debug router navigation
- Track performance

### Network Tab

Monitor API requests:
- Check request headers (Authorization)
- Verify response status codes
- Inspect request/response payloads

## Next Steps

1. Test all login flows
2. Verify resource tree rendering
3. Test permission granting/revoking
4. Test navigation guards
5. Verify logout functionality
