<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation Bar -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <!-- Logo -->
            <div class="flex-shrink-0 flex items-center">
              <h1 class="text-xl font-bold text-primary-600">ACL POC</h1>
            </div>

            <!-- Navigation Links -->
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <router-link
                to="/dashboard"
                class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="isActive('/dashboard') ? activeClass : inactiveClass"
              >
                Dashboard
              </router-link>
              <router-link
                to="/resources"
                class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="isActive('/resources') ? activeClass : inactiveClass"
              >
                Resources
              </router-link>
              <router-link
                to="/permissions"
                class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="isActive('/permissions') ? activeClass : inactiveClass"
              >
                My Permissions
              </router-link>
            </div>
          </div>

          <!-- User Menu -->
          <div class="flex items-center">
            <span class="text-sm text-gray-700 mr-4">
              Welcome, <span class="font-medium">{{ authStore.username }}</span>
            </span>
            <button @click="handleLogout" class="btn-secondary btn-sm">
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Page Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeClass = 'border-primary-500 text-gray-900'
const inactiveClass = 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'

function isActive(path: string): boolean {
  return route.path === path
}

function handleLogout(): void {
  authStore.logout()
  router.push('/login')
}
</script>
