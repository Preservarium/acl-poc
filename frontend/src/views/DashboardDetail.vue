<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import PermissionList from '@/components/PermissionList.vue'
import PermissionGrant from '@/components/PermissionGrant.vue'
import { fetchDashboard, updateDashboard, deleteDashboard } from '@/api/dashboards'
import { fetchResourcePermissions, revokePermission } from '@/api/permissions'
import type { Dashboard, Permission } from '@/types'

const route = useRoute()
const router = useRouter()

const dashboardId = computed(() => route.params.id as string)
const dashboard = ref<Dashboard | null>(null)
const permissions = ref<Permission[]>([])

const loading = ref(false)
const error = ref<string | null>(null)

// Edit mode state
const isEditing = ref(false)
const editForm = ref({
  name: '',
  config: '{}'
})
const saving = ref(false)
const editError = ref<string | null>(null)

const loadDashboardDetails = async () => {
  loading.value = true
  error.value = null

  try {
    const [dashboardData, permissionsData] = await Promise.all([
      fetchDashboard(dashboardId.value),
      fetchResourcePermissions('dashboard', dashboardId.value)
    ])

    dashboard.value = dashboardData
    permissions.value = permissionsData
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load dashboard details'
  } finally {
    loading.value = false
  }
}

const startEditing = () => {
  if (dashboard.value) {
    editForm.value = {
      name: dashboard.value.name,
      config: JSON.stringify(dashboard.value.config, null, 2)
    }
    editError.value = null
    isEditing.value = true
  }
}

const cancelEditing = () => {
  isEditing.value = false
  editError.value = null
}

const handleSave = async () => {
  if (!editForm.value.name.trim()) {
    editError.value = 'Dashboard name is required'
    return
  }

  // Validate JSON config
  let config: Record<string, any> = {}
  try {
    config = JSON.parse(editForm.value.config)
  } catch (err) {
    editError.value = 'Invalid JSON configuration'
    return
  }

  saving.value = true
  editError.value = null

  try {
    await updateDashboard(dashboardId.value, {
      name: editForm.value.name,
      config
    })

    await loadDashboardDetails()
    isEditing.value = false
  } catch (err: any) {
    editError.value = err.response?.data?.detail || 'Failed to update dashboard'
  } finally {
    saving.value = false
  }
}

const handleDelete = async () => {
  if (!confirm('Are you sure you want to delete this dashboard? This action cannot be undone.')) {
    return
  }

  try {
    await deleteDashboard(dashboardId.value)
    router.push({ name: 'Dashboards' })
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete dashboard'
  }
}

const handleRevokePermission = async (permissionId: string) => {
  if (!confirm('Are you sure you want to revoke this permission?')) {
    return
  }

  try {
    await revokePermission(permissionId)
    await loadDashboardDetails()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to revoke permission'
  }
}

const handlePermissionGranted = async () => {
  await loadDashboardDetails()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const configString = computed(() => {
  if (!dashboard.value) return ''
  return JSON.stringify(dashboard.value.config, null, 2)
})

onMounted(() => {
  loadDashboardDetails()
})
</script>

<template>
  <AppLayout>
    <div class="container mx-auto px-4 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading dashboard details...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="loadDashboardDetails"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Dashboard Details -->
      <div v-else-if="dashboard" class="space-y-6">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <button
                @click="router.back()"
                class="text-gray-400 hover:text-gray-600 transition-colors"
              >
                ← Back
              </button>
              <span class="text-3xl">📊</span>
              <h1 class="text-3xl font-bold text-gray-800">{{ dashboard.name }}</h1>
            </div>
            <div class="flex gap-2">
              <button
                v-if="!isEditing"
                @click="startEditing"
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Edit
              </button>
              <button
                @click="handleDelete"
                class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-500">Created By:</span>
              <span class="ml-2 text-gray-800">{{ dashboard.created_by }}</span>
            </div>
            <div>
              <span class="text-gray-500">Created:</span>
              <span class="ml-2 text-gray-800">{{ formatDate(dashboard.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- Edit Form or View Mode -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Dashboard Configuration</h2>

          <!-- View Mode -->
          <div v-if="!isEditing">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <div class="px-3 py-2 bg-gray-50 rounded-md">{{ dashboard.name }}</div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Configuration</label>
              <pre class="px-3 py-2 bg-gray-50 rounded-md overflow-x-auto text-sm font-mono">{{ configString }}</pre>
            </div>
          </div>

          <!-- Edit Mode -->
          <div v-else>
            <!-- Error Message -->
            <div v-if="editError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {{ editError }}
            </div>

            <form @submit.prevent="handleSave" class="space-y-4">
              <!-- Name Field -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Dashboard Name
                </label>
                <input
                  v-model="editForm.name"
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
                  v-model="editForm.config"
                  rows="10"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"key": "value"}'
                />
                <p class="text-xs text-gray-500 mt-1">Enter a valid JSON object</p>
              </div>

              <!-- Buttons -->
              <div class="flex justify-end gap-3">
                <button
                  type="button"
                  @click="cancelEditing"
                  class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :disabled="saving"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {{ saving ? 'Saving...' : 'Save Changes' }}
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- Permissions Section -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Permissions</h2>
          <p class="text-gray-600 mb-4">Manage who has access to this dashboard:</p>

          <!-- Current Permissions -->
          <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-3">Current Permissions</h3>
            <PermissionList
              :permissions="permissions"
              :loading="false"
              @revoke="handleRevokePermission"
            />
          </div>

          <!-- Grant Permission -->
          <div>
            <h3 class="text-lg font-semibold text-gray-800 mb-3">Grant New Permission</h3>
            <PermissionGrant
              resource-type="dashboard"
              :resource-id="dashboardId"
              @granted="handlePermissionGranted"
            />
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
