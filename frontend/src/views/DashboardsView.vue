<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { fetchDashboards, createDashboard, deleteDashboard } from '@/api/dashboards'
import type { Dashboard } from '@/types'

const router = useRouter()

const dashboards = ref<Dashboard[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Create dashboard modal state
const showCreateModal = ref(false)
const createForm = ref({
  name: '',
  config: '{}'
})
const creating = ref(false)
const createError = ref<string | null>(null)

const loadDashboards = async () => {
  loading.value = true
  error.value = null

  try {
    dashboards.value = await fetchDashboards()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load dashboards'
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  createForm.value = { name: '', config: '{}' }
  createError.value = null
  showCreateModal.value = true
}

const handleCreateDashboard = async () => {
  if (!createForm.value.name.trim()) {
    createError.value = 'Dashboard name is required'
    return
  }

  // Validate JSON config
  let config: Record<string, any> = {}
  try {
    config = JSON.parse(createForm.value.config)
  } catch (err) {
    createError.value = 'Invalid JSON configuration'
    return
  }

  creating.value = true
  createError.value = null

  try {
    await createDashboard({
      name: createForm.value.name,
      config
    })

    await loadDashboards()
    showCreateModal.value = false
  } catch (err: any) {
    createError.value = err.response?.data?.detail || 'Failed to create dashboard'
  } finally {
    creating.value = false
  }
}

const handleDeleteDashboard = async (dashboardId: string) => {
  if (!confirm('Are you sure you want to delete this dashboard?')) {
    return
  }

  try {
    await deleteDashboard(dashboardId)
    await loadDashboards()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete dashboard'
  }
}

const viewDashboard = (dashboardId: string) => {
  router.push({ name: 'DashboardDetail', params: { id: dashboardId } })
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

onMounted(() => {
  loadDashboards()
})
</script>

<template>
  <AppLayout>
    <div class="container mx-auto px-4 py-8">
      <div class="bg-white rounded-lg shadow-md p-6">
        <!-- Header -->
        <div class="flex items-center justify-between mb-6">
          <div>
            <h1 class="text-3xl font-bold text-gray-800">Dashboards</h1>
            <p class="text-gray-600 mt-1">Manage your custom dashboards</p>
          </div>
          <button
            @click="openCreateModal"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + Create Dashboard
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="loading" class="text-center py-12 text-gray-500">
          Loading dashboards...
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
          <p class="text-red-700 mb-4">{{ error }}</p>
          <button
            @click="loadDashboards"
            class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>

        <!-- Empty State -->
        <div v-else-if="dashboards.length === 0" class="text-center py-12">
          <div class="text-6xl mb-4">📊</div>
          <h2 class="text-xl font-semibold text-gray-800 mb-2">No Dashboards Yet</h2>
          <p class="text-gray-600 mb-4">Create your first dashboard to get started</p>
          <button
            @click="openCreateModal"
            class="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Create Dashboard
          </button>
        </div>

        <!-- Dashboard Grid -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="dashboard in dashboards"
            :key="dashboard.id"
            class="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow cursor-pointer"
            @click="viewDashboard(dashboard.id)"
          >
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center gap-3">
                <span class="text-3xl">📊</span>
                <div>
                  <h3 class="text-lg font-semibold text-gray-800">{{ dashboard.name }}</h3>
                  <p class="text-xs text-gray-500">Created by {{ dashboard.created_by }}</p>
                </div>
              </div>
              <button
                @click.stop="handleDeleteDashboard(dashboard.id)"
                class="text-red-600 hover:bg-red-50 px-2 py-1 rounded transition-colors"
                title="Delete dashboard"
              >
                ×
              </button>
            </div>

            <div class="text-xs text-gray-500">
              Created {{ formatDate(dashboard.created_at) }}
            </div>

            <div class="mt-4 pt-4 border-t border-gray-200">
              <span class="text-xs text-blue-600 hover:text-blue-700 font-medium">
                View Details →
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Create Dashboard Modal -->
      <Transition name="modal">
        <div
          v-if="showCreateModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          @click.self="showCreateModal = false"
        >
          <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <!-- Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 class="text-xl font-bold text-gray-800">Create New Dashboard</h2>
              <button
                @click="showCreateModal = false"
                class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <!-- Content -->
            <div class="p-6">
              <!-- Error Message -->
              <div v-if="createError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {{ createError }}
              </div>

              <form @submit.prevent="handleCreateDashboard" class="space-y-4">
                <!-- Name Field -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Dashboard Name
                  </label>
                  <input
                    v-model="createForm.name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter dashboard name"
                  />
                </div>

                <!-- Config Field -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Configuration (JSON)
                  </label>
                  <textarea
                    v-model="createForm.config"
                    rows="5"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    placeholder='{"key": "value"}'
                  />
                  <p class="text-xs text-gray-500 mt-1">Enter a valid JSON object</p>
                </div>

                <!-- Buttons -->
                <div class="flex justify-end gap-3">
                  <button
                    type="button"
                    @click="showCreateModal = false"
                    class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    :disabled="creating"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {{ creating ? 'Creating...' : 'Create' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </AppLayout>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.9);
}
</style>
