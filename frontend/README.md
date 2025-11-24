# ACL POC Frontend

Vue 3 + TypeScript + Vite + Pinia + TailwindCSS frontend for the Access Control List Proof of Concept.

## Features

- Modern Vue 3 with Composition API and `<script setup>`
- TypeScript for type safety
- Pinia for state management
- Vue Router with navigation guards
- Axios with authentication interceptors
- TailwindCSS for styling
- Responsive design

## Project Structure

```
frontend/
├── src/
│   ├── api/                  # API client modules
│   │   ├── client.ts         # Axios setup with interceptors
│   │   ├── auth.ts           # Authentication API
│   │   ├── permissions.ts    # Permissions API
│   │   ├── resources.ts      # Resources API
│   │   └── users.ts          # Users API
│   │
│   ├── stores/               # Pinia stores
│   │   ├── auth.ts           # Authentication state
│   │   ├── permissions.ts    # Permissions state
│   │   └── resources.ts      # Resources state
│   │
│   ├── components/           # Vue components
│   │   ├── AppLayout.vue     # Main layout with nav
│   │   ├── LoginForm.vue     # Login form
│   │   ├── ResourceTree.vue  # Hierarchical resource tree
│   │   ├── PermissionList.vue    # List of permissions
│   │   ├── PermissionGrant.vue   # Grant permission form
│   │   └── PermissionManager.vue # Permission management modal
│   │
│   ├── views/                # Page views
│   │   ├── LoginView.vue     # Login page
│   │   ├── DashboardView.vue # Dashboard
│   │   ├── ResourcesView.vue # Resources management
│   │   └── PermissionsView.vue # My permissions view
│   │
│   ├── router/
│   │   └── index.ts          # Vue Router config
│   │
│   ├── types.ts              # TypeScript type definitions
│   ├── main.ts               # App entry point
│   └── App.vue               # Root component
│
├── Dockerfile                # Production Docker build
├── nginx.conf                # Nginx configuration
├── vite.config.ts            # Vite configuration
├── tailwind.config.js        # TailwindCSS config
└── package.json              # Dependencies
```

## Setup

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000 (or configure VITE_API_URL)

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Update .env with your API URL if different
# VITE_API_URL=http://localhost:8000
```

### Development

```bash
# Start dev server with hot reload
npm run dev

# Access at http://localhost:5173
```

### Build for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker

```bash
# Build Docker image
docker build -t acl-poc-frontend .

# Run container
docker run -p 8080:80 acl-poc-frontend
```

## Key Features

### Authentication

- JWT-based authentication
- Token stored in localStorage
- Automatic token refresh via axios interceptors
- Protected routes with navigation guards
- Auto-redirect to login on 401 errors

### State Management

The app uses Pinia stores for:

- **Auth Store**: User authentication state and actions
- **Permissions Store**: Permission management and caching
- **Resources Store**: Resource tree and CRUD operations

### API Client

Axios instance with:
- Base URL configuration
- Request interceptor for JWT tokens
- Response interceptor for error handling
- Automatic 401 redirect to login

### Components

- **AppLayout**: Main layout with navigation and user menu
- **LoginForm**: Username/password authentication
- **ResourceTree**: Hierarchical resource display with expand/collapse
- **PermissionList**: Display permissions for a resource
- **PermissionGrant**: Form to grant new permissions
- **PermissionManager**: Modal for managing resource permissions

### Views

- **LoginView**: Login page with branding
- **DashboardView**: Overview with stats and quick actions
- **ResourcesView**: Manage resources in tree structure
- **PermissionsView**: View all user's permissions (direct and via groups)

## Demo Users

- alice / password
- bob / password

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: `/api`)

## Technology Stack

- **Vue 3**: Progressive JavaScript framework
- **TypeScript**: Type safety and better developer experience
- **Vite**: Fast build tool and dev server
- **Pinia**: Intuitive state management
- **Vue Router**: Official routing library
- **Axios**: Promise-based HTTP client
- **TailwindCSS**: Utility-first CSS framework

## Development Notes

### Code Style

- Uses Vue 3 Composition API with `<script setup>`
- TypeScript for all logic files
- TailwindCSS for styling (no custom CSS unless necessary)
- Reactive state with `ref` and `reactive`
- Composable pattern for reusable logic

### Type Safety

All API responses and component props are fully typed using TypeScript interfaces defined in `src/types.ts`.

### Error Handling

- API errors are caught and displayed to users
- Network errors show user-friendly messages
- 401 errors automatically redirect to login
- Loading states for all async operations

## License

MIT
