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
