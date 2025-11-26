<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { fetchPermissionMatrix } from '@/api/permissions'
import { fetchSites } from '@/api/resources'
import type { PermissionMatrixResponse, MatrixPermissionInfo, Site } from '@/types'

const loading = ref(false)
const error = ref<string | null>(null)
const matrixData = ref<PermissionMatrixResponse | null>(null)
const sites = ref<Site[]>([])

// Filter states
const selectedResourceType = ref<string>('site')
const selectedResourceId = ref<string>('')

// Available resource types for filter
const resourceTypes = [
  { value: 'site', label: 'Sites', icon: '🏭' },
  { value: 'plan', label: 'Plans', icon: '📋' },
  { value: 'sensor', label: 'Sensors', icon: '📡' },
  { value: 'broker', label: 'Brokers', icon: '📶' },
  { value: 'alarm', label: 'Alarms', icon: '🔔' },
  { value: 'dashboard', label: 'Dashboards', icon: '📊' }
]

// Permission columns
const permissionColumns = [
  { key: 'read', label: 'Read' },
  { key: 'write', label: 'Write' },
  { key: 'delete', label: 'Delete' },
  { key: 'create', label: 'Create' },
  { key: 'manage', label: 'Manage' }
]

const loadSites = async () => {
  try {
    sites.value = await fetchSites()
    if (sites.value.length > 0 && !selectedResourceId.value) {
      selectedResourceId.value = sites.value[0].id
    }
  } catch (err: any) {
    console.error('Failed to load sites:', err)
  }
}

const loadMatrix = async () => {
  if (!selectedResourceId.value) return

  loading.value = true
  error.value = null
  try {
    matrixData.value = await fetchPermissionMatrix(selectedResourceType.value, selectedResourceId.value)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load permission matrix'
  } finally {
    loading.value = false
  }
}

const getGranteeIcon = (granteeType: string) => {
  return granteeType === 'group' ? '👥' : '👤'
}

const getCellSymbol = (permInfo: MatrixPermissionInfo) => {
  if (!permInfo.allowed) {
    return { symbol: '-', tooltip: 'Not granted', class: 'text-gray-400' }
  }

  if (permInfo.inherited && permInfo.has_field_restrictions) {
    return {
      symbol: '✓i*',
      tooltip: `Inherits from ${permInfo.source || 'parent'} with field restrictions`,
      class: 'text-blue-600'
    }
  }

  if (permInfo.inherited) {
    return {
      symbol: '✓i',
      tooltip: `Inherits from ${permInfo.source || 'parent'}`,
      class: 'text-blue-600'
    }
  }

  if (permInfo.has_field_restrictions) {
    return {
      symbol: '✓*',
      tooltip: `Allowed with field restrictions: ${permInfo.fields?.join(', ') || 'specific fields'}`,
      class: 'text-green-600'
    }
  }

  return {
    symbol: '✓',
    tooltip: 'Allowed',
    class: 'text-green-600'
  }
}

const availableResources = computed(() => {
  // For now, only show sites. Could be extended to load other resource types
  if (selectedResourceType.value === 'site') {
    return sites.value.map(s => ({ id: s.id, name: s.name }))
  }
  return []
})

onMounted(async () => {
  await loadSites()
  if (selectedResourceId.value) {
    await loadMatrix()
  }
})

const onResourceTypeChange = async () => {
  selectedResourceId.value = ''
  // Load resources for the selected type
  if (selectedResourceType.value === 'site') {
    await loadSites()
  }
  // Could extend to load other resource types here
}

const onResourceChange = async () => {
  await loadMatrix()
}

const handleCellClick = (granteeId: string, granteeType: string, permission: string) => {
  // TODO: Open modal to edit permission
  console.log('Edit permission:', { granteeId, granteeType, permission })
}
</script>

<template>
  <div class="permission-matrix">
    <!-- Header with filters -->
    <div class="mb-6 pb-4 border-b border-gray-200">
      <h2 class="text-2xl font-bold text-gray-800 mb-4">Permission Matrix</h2>

      <div class="flex gap-4 items-center">
        <!-- Resource Type Filter -->
        <div class="flex-none">
          <label class="block text-sm font-medium text-gray-700 mb-1">Resource Type</label>
          <select
            v-model="selectedResourceType"
            @change="onResourceTypeChange"
            class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="type in resourceTypes" :key="type.value" :value="type.value">
              {{ type.icon }} {{ type.label }}
            </option>
          </select>
        </div>

        <!-- Resource Instance Filter -->
        <div class="flex-1 min-w-0">
          <label class="block text-sm font-medium text-gray-700 mb-1">
            {{ resourceTypes.find(t => t.value === selectedResourceType)?.label || 'Resource' }}
          </label>
          <select
            v-model="selectedResourceId"
            @change="onResourceChange"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            :disabled="availableResources.length === 0"
          >
            <option value="" disabled>Select a resource...</option>
            <option v-for="resource in availableResources" :key="resource.id" :value="resource.id">
              {{ resource.name }}
            </option>
          </select>
        </div>

        <!-- Refresh Button -->
        <div class="flex-none self-end">
          <button
            @click="loadMatrix"
            :disabled="!selectedResourceId || loading"
            class="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            🔄 Refresh
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12 text-gray-500">
      Loading permission matrix...
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-red-600 mb-4">{{ error }}</p>
      <button
        @click="loadMatrix"
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
      >
        Try Again
      </button>
    </div>

    <!-- Matrix Table -->
    <div v-else-if="matrixData" class="space-y-4">
      <!-- Resource Info -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p class="text-sm text-blue-900">
          <strong>Resource:</strong> {{ matrixData.resource_name }}
          <span class="text-blue-700 ml-2">({{ matrixData.resource_type }})</span>
        </p>
      </div>

      <!-- Matrix Grid with Horizontal Scroll -->
      <div class="overflow-x-auto border border-gray-200 rounded-lg">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th
                class="sticky left-0 z-10 bg-gray-50 px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200"
                style="min-width: 200px;"
              >
                Grantee
              </th>
              <th
                v-for="col in permissionColumns"
                :key="col.key"
                class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider"
                style="min-width: 100px;"
              >
                {{ col.label }}
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr
              v-for="row in matrixData.grantees"
              :key="row.grantee.grantee_id"
              class="hover:bg-gray-50"
            >
              <!-- Grantee Name (Sticky) -->
              <td class="sticky left-0 z-10 bg-white px-6 py-4 whitespace-nowrap border-r border-gray-200">
                <div class="flex items-center gap-2">
                  <span class="text-lg">{{ getGranteeIcon(row.grantee.grantee_type) }}</span>
                  <span class="text-sm font-medium text-gray-900">
                    {{ row.grantee.grantee_name }}
                  </span>
                </div>
              </td>

              <!-- Permission Cells -->
              <td
                v-for="col in permissionColumns"
                :key="col.key"
                class="px-6 py-4 text-center cursor-pointer hover:bg-blue-50"
                @click="handleCellClick(row.grantee.grantee_id, row.grantee.grantee_type, col.key)"
                :title="getCellSymbol(row.permissions[col.key as keyof typeof row.permissions]).tooltip"
              >
                <span
                  :class="[
                    'text-lg font-semibold',
                    getCellSymbol(row.permissions[col.key as keyof typeof row.permissions]).class
                  ]"
                >
                  {{ getCellSymbol(row.permissions[col.key as keyof typeof row.permissions]).symbol }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Legend -->
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 class="text-sm font-semibold text-gray-700 mb-2">Legend</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div class="flex items-center gap-2">
            <span class="text-green-600 font-semibold">✓</span>
            <span class="text-gray-600">Allowed</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-blue-600 font-semibold">✓i</span>
            <span class="text-gray-600">Inherits</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-green-600 font-semibold">✓*</span>
            <span class="text-gray-600">Field restrictions</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-gray-400 font-semibold">-</span>
            <span class="text-gray-600">Not granted</span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div
        v-if="matrixData.grantees.length === 0"
        class="text-center py-12 text-gray-500 bg-gray-50 rounded-lg"
      >
        <p class="text-lg">No permissions found</p>
        <p class="text-sm mt-2">No users or groups have been granted permissions on this resource.</p>
      </div>
    </div>

    <!-- No Resource Selected State -->
    <div v-else class="text-center py-12 text-gray-500 bg-gray-50 rounded-lg">
      <p class="text-lg">Select a resource to view its permission matrix</p>
    </div>
  </div>
</template>

<style scoped>
.permission-matrix {
  @apply w-full;
}

/* Ensure sticky column works properly */
.sticky {
  position: sticky;
  background-color: inherit;
}

/* Add shadow to sticky column for better visual separation */
.sticky::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  bottom: -1px;
  width: 1px;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.1);
}

/* Improve table cell alignment */
table {
  border-collapse: separate;
  border-spacing: 0;
}

/* Ensure hover state works on sticky cells too */
tr:hover .sticky {
  background-color: #f9fafb;
}
</style>
