<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Top Navigation Bar -->
    <nav class="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
      <div class="px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <!-- Logo -->
            <div class="flex-shrink-0 flex items-center">
              <h1 class="text-xl font-bold text-primary-600">PRESERVARIUM</h1>
            </div>

            <!-- Navigation Links -->
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <router-link
                to="/dashboard"
                class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="isActive('/dashboard') ? activeClass : inactiveClass"
              >
                📊 Dashboard
              </router-link>
              <router-link
                to="/groups"
                class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="isActive('/groups') ? activeClass : inactiveClass"
              >
                👥 Groups
              </router-link>
              <router-link
                v-if="authStore.user?.is_admin"
                to="/users"
                class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="isActive('/users') ? activeClass : inactiveClass"
              >
                👤 Users
              </router-link>
              <router-link
                to="/permissions"
                class="inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                :class="isActive('/permissions') ? activeClass : inactiveClass"
              >
                🔐 Permissions
              </router-link>
            </div>
          </div>

          <!-- User Menu -->
          <div class="flex items-center">
            <span class="text-sm text-gray-700 mr-4">
              👤 <span class="font-medium">{{ authStore.username }}</span>
            </span>
            <button @click="handleLogout" class="btn-secondary btn-sm">
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Layout with Sidebar -->
    <div class="flex flex-1 overflow-hidden">
      <!-- Sidebar -->
      <aside class="w-64 flex-shrink-0 bg-white border-r border-gray-200 overflow-y-auto">
        <SidebarTree ref="sidebarTreeRef" />
      </aside>

      <!-- Main Content Area -->
      <main class="flex-1 overflow-y-auto bg-gray-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import SidebarTree from './SidebarTree.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const sidebarTreeRef = ref<InstanceType<typeof SidebarTree> | null>(null)

const activeClass = 'border-primary-500 text-gray-900'
const inactiveClass = 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'

function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(path)
}

function handleLogout(): void {
  authStore.logout()
  router.push('/login')
}

// Expose method to refresh sidebar
defineExpose({
  refreshSidebar: () => sidebarTreeRef.value?.refresh()
})
</script>
