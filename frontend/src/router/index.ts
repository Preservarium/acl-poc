import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/access-denied',
    name: 'AccessDenied',
    component: () => import('@/views/AccessDenied.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/resources',
    name: 'resources',
    component: () => import('@/views/ResourcesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/permissions',
    name: 'permissions',
    component: () => import('@/views/PermissionsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/groups',
    name: 'groups',
    component: () => import('@/views/GroupsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/groups/:id',
    name: 'GroupDetail',
    component: () => import('@/views/GroupDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('@/views/UsersView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users/:id',
    name: 'UserDetail',
    component: () => import('@/views/UserDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/sites/:id/:tab?',
    name: 'SiteDetail',
    component: () => import('@/views/SiteDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/plans/:id/:tab?',
    name: 'PlanDetail',
    component: () => import('@/views/PlanDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/sensors/:id',
    name: 'SensorDetail',
    component: () => import('@/views/SensorDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/alarms/:id',
    name: 'AlarmDetail',
    component: () => import('@/views/AlarmDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/brokers/:id',
    name: 'BrokerDetail',
    component: () => import('@/views/BrokerDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboards',
    name: 'Dashboards',
    component: () => import('@/views/DashboardsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboards/:id',
    name: 'DashboardDetail',
    component: () => import('@/views/DashboardDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/audit-logs',
    name: 'AuditLogs',
    component: () => import('@/views/AuditLogView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Check if route requires authentication
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth) {
    // If not authenticated, redirect to login
    if (!authStore.isAuthenticated) {
      // Try to initialize auth from stored token
      if (authStore.token) {
        try {
          await authStore.initialize()
          next()
        } catch {
          next({ name: 'login', query: { redirect: to.fullPath } })
        }
      } else {
        next({ name: 'login', query: { redirect: to.fullPath } })
      }
    } else {
      next()
    }
  } else {
    // If already authenticated and trying to access login, redirect to dashboard
    if (to.name === 'login' && authStore.isAuthenticated) {
      next({ name: 'dashboard' })
    } else {
      next()
    }
  }
})

export default router
