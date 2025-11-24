<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { fetchSites, fetchPlans, fetchSensors } from '@/api/resources'
import { fetchMyPermissions } from '@/api/permissions'
import AppLayout from '@/components/AppLayout.vue'

const router = useRouter()
const authStore = useAuthStore()

const currentUser = computed(() => authStore.user)

const stats = ref({
  sites: 0,
  plans: 0,
  sensors: 0,
  directPermissions: 0,
  groupPermissions: 0
})

const loading = ref(false)
const error = ref<string | null>(null)

const loadDashboardData = async () => {
  loading.value = true
  error.value = null

  try {
    const [sites, plans, sensors, permissions] = await Promise.all([
      fetchSites(),
      fetchPlans(),
      fetchSensors(),
      fetchMyPermissions()
    ])

    stats.value = {
      sites: sites.length,
      plans: plans.length,
      sensors: sensors.length,
      directPermissions: permissions.direct.length,
      groupPermissions: permissions.via_groups.length
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load dashboard data'
  } finally {
    loading.value = false
  }
}

const navigateTo = (route: string) => {
  router.push(route)
}

onMounted(() => {
  loadDashboardData()
})
</script>

<template>
  <AppLayout>
    <div class="container mx-auto px-4 py-8">
    <div class="max-w-6xl mx-auto">
      <!-- Welcome Section -->
      <div class="bg-white rounded-lg shadow-md p-8 mb-6">
        <h1 class="text-4xl font-bold text-gray-800 mb-2">
          Welcome, {{ currentUser?.username || 'User' }}!
        </h1>
        <p class="text-gray-600 text-lg">
          {{ currentUser?.is_admin ? '🛡️ Administrator Account' : '👤 User Account' }}
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading dashboard...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="loadDashboardData"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Stats Grid -->
      <div v-else>
        <!-- Resource Statistics -->
        <div class="mb-6">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Accessible Resources</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Sites Card -->
            <div
              class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
              @click="navigateTo('/resources')"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-sm font-medium uppercase">Sites</p>
                  <p class="text-4xl font-bold text-gray-800 mt-2">{{ stats.sites }}</p>
                </div>
                <div class="text-5xl">🏭</div>
              </div>
              <p class="text-gray-600 text-sm mt-4">
                Click to view all sites
              </p>
            </div>

            <!-- Plans Card -->
            <div
              class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
              @click="navigateTo('/resources')"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-sm font-medium uppercase">Plans</p>
                  <p class="text-4xl font-bold text-gray-800 mt-2">{{ stats.plans }}</p>
                </div>
                <div class="text-5xl">📋</div>
              </div>
              <p class="text-gray-600 text-sm mt-4">
                Total plans across all sites
              </p>
            </div>

            <!-- Sensors Card -->
            <div
              class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
              @click="navigateTo('/resources')"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-sm font-medium uppercase">Sensors</p>
                  <p class="text-4xl font-bold text-gray-800 mt-2">{{ stats.sensors }}</p>
                </div>
                <div class="text-5xl">📡</div>
              </div>
              <p class="text-gray-600 text-sm mt-4">
                Total sensors across all plans
              </p>
            </div>
          </div>
        </div>

        <!-- Permission Statistics -->
        <div>
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Your Permissions</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Direct Permissions Card -->
            <div
              class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
              @click="navigateTo('/permissions')"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-sm font-medium uppercase">Direct Permissions</p>
                  <p class="text-4xl font-bold text-gray-800 mt-2">{{ stats.directPermissions }}</p>
                </div>
                <div class="text-5xl">👤</div>
              </div>
              <p class="text-gray-600 text-sm mt-4">
                Permissions granted directly to you
              </p>
            </div>

            <!-- Group Permissions Card -->
            <div
              class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
              @click="navigateTo('/permissions')"
            >
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-gray-500 text-sm font-medium uppercase">Via Groups</p>
                  <p class="text-4xl font-bold text-gray-800 mt-2">{{ stats.groupPermissions }}</p>
                </div>
                <div class="text-5xl">👥</div>
              </div>
              <p class="text-gray-600 text-sm mt-4">
                Permissions inherited from group membership
              </p>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Quick Actions</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              @click="navigateTo('/resources')"
              class="px-6 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-left"
            >
              <div class="flex items-center gap-3">
                <span class="text-2xl">🏭</span>
                <div>
                  <p class="font-semibold">Manage Resources</p>
                  <p class="text-sm text-blue-100">View and manage sites, plans, and sensors</p>
                </div>
              </div>
            </button>

            <button
              @click="navigateTo('/permissions')"
              class="px-6 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-left"
            >
              <div class="flex items-center gap-3">
                <span class="text-2xl">🔑</span>
                <div>
                  <p class="font-semibold">View My Permissions</p>
                  <p class="text-sm text-purple-100">See all permissions you have access to</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
  </AppLayout>
</template>
