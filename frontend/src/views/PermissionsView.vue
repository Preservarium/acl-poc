<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { fetchMyPermissions } from '@/api/permissions'
import type { MyPermission } from '@/types'

const directPermissions = ref<MyPermission[]>([])
const groupPermissions = ref<MyPermission[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const loadPermissions = async () => {
  loading.value = true
  error.value = null
  try {
    const data = await fetchMyPermissions()
    directPermissions.value = data.direct
    groupPermissions.value = data.via_groups
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load permissions'
  } finally {
    loading.value = false
  }
}

const getResourceIcon = (type: string) => {
  switch (type) {
    case 'site': return '🏭'
    case 'plan': return '📋'
    case 'sensor': return '📡'
    default: return '📄'
  }
}

const getPermissionColor = (permission: string) => {
  switch (permission) {
    case 'manage': return 'bg-purple-100 text-purple-800'
    case 'read': return 'bg-blue-100 text-blue-800'
    case 'write': return 'bg-green-100 text-green-800'
    case 'create': return 'bg-orange-100 text-orange-800'
    case 'delete': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

onMounted(() => {
  loadPermissions()
})
</script>

<template>
  <AppLayout>
  <div class="container mx-auto px-4 py-8">
    <div class="bg-white rounded-lg shadow-md p-6">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-3xl font-bold text-gray-800">My Permissions</h1>
        <button
          @click="loadPermissions"
          class="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
        >
          🔄 Refresh
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading your permissions...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <p class="text-red-600 mb-4">{{ error }}</p>
        <button
          @click="loadPermissions"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Permissions Display -->
      <div v-else class="space-y-8">
        <!-- Direct Permissions Section -->
        <div>
          <h2 class="text-xl font-semibold text-gray-800 mb-4">Direct Permissions</h2>

          <!-- Empty State -->
          <div v-if="directPermissions.length === 0" class="text-center py-8 text-gray-500 border border-gray-200 rounded-lg">
            You have no direct permissions assigned
          </div>

          <!-- Permissions Table -->
          <div v-else class="border rounded-lg overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Resource
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Permission
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Inherit
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Via
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="(perm, index) in directPermissions" :key="index" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <span class="text-xl">{{ getResourceIcon(perm.resource_type) }}</span>
                      <div>
                        <div class="text-sm font-medium text-gray-900">{{ perm.resource_name }}</div>
                        <div class="text-xs text-gray-500">{{ perm.resource_type }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full" :class="getPermissionColor(perm.permission)">
                      {{ perm.permission }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span v-if="perm.inherit" class="text-green-600 text-lg">✓</span>
                    <span v-else class="text-gray-300 text-lg">−</span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {{ perm.via }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Via Groups Section -->
        <div>
          <h2 class="text-xl font-semibold text-gray-800 mb-4">Via Groups</h2>

          <!-- Empty State -->
          <div v-if="groupPermissions.length === 0" class="text-center py-8 text-gray-500 border border-gray-200 rounded-lg">
            You have no permissions inherited from groups
          </div>

          <!-- Permissions Table -->
          <div v-else class="border rounded-lg overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Resource
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Permission
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Inherit
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Via
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="(perm, index) in groupPermissions" :key="index" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <span class="text-xl">{{ getResourceIcon(perm.resource_type) }}</span>
                      <div>
                        <div class="text-sm font-medium text-gray-900">{{ perm.resource_name }}</div>
                        <div class="text-xs text-gray-500">{{ perm.resource_type }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full" :class="getPermissionColor(perm.permission)">
                      {{ perm.permission }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span v-if="perm.inherit" class="text-green-600 text-lg">✓</span>
                    <span v-else class="text-gray-300 text-lg">−</span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      👥 {{ perm.via }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
  </AppLayout>
</template>
