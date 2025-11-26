<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { ExpiringPermission } from '@/types'
import { fetchExpiringPermissions } from '@/api/permissions'
import { grantPermission } from '@/api/permissions'

// State
const permissions = ref<ExpiringPermission[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const daysFilter = ref(7)
const groupBy = ref<'user' | 'resource'>('user')

// Available filter options
const filterOptions = [
  { value: 7, label: '7 days' },
  { value: 14, label: '14 days' },
  { value: 30, label: '30 days' },
  { value: 90, label: '90 days' },
]

// Load expiring permissions
const loadPermissions = async () => {
  loading.value = true
  error.value = null

  try {
    permissions.value = await fetchExpiringPermissions(daysFilter.value)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load expiring permissions'
    console.error('Error loading expiring permissions:', err)
  } finally {
    loading.value = false
  }
}

// Group permissions by user/group
const groupedByGrantee = computed(() => {
  const groups: Record<string, ExpiringPermission[]> = {}

  permissions.value.forEach(perm => {
    const key = `${perm.grantee_type}:${perm.grantee_id}`
    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push(perm)
  })

  return groups
})

// Group permissions by resource
const groupedByResource = computed(() => {
  const groups: Record<string, ExpiringPermission[]> = {}

  permissions.value.forEach(perm => {
    const key = `${perm.resource_type}:${perm.resource_id}`
    if (!groups[key]) {
      groups[key] = []
    }
    groups[key].push(perm)
  })

  return groups
})

// Format date
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Get urgency color class based on days until expiry
const getUrgencyClass = (days: number) => {
  if (days <= 1) return 'text-red-600 font-bold'
  if (days <= 3) return 'text-orange-600 font-semibold'
  if (days <= 7) return 'text-yellow-600'
  return 'text-gray-600'
}

// Get urgency badge class
const getUrgencyBadge = (days: number) => {
  if (days <= 1) return 'bg-red-100 text-red-800 border-red-200'
  if (days <= 3) return 'bg-orange-100 text-orange-800 border-orange-200'
  if (days <= 7) return 'bg-yellow-100 text-yellow-800 border-yellow-200'
  return 'bg-blue-100 text-blue-800 border-blue-200'
}

// Extend permission expiration (by adding 30 days)
const extendExpiration = async (permission: ExpiringPermission) => {
  if (!confirm(`Extend this permission by 30 days?`)) {
    return
  }

  try {
    // Calculate new expiration date (current + 30 days)
    const currentExpiry = new Date(permission.expires_at)
    const newExpiry = new Date(currentExpiry.getTime() + 30 * 24 * 60 * 60 * 1000)

    // Grant a new permission with extended expiration
    // Note: In a production system, you'd want an "extend" endpoint
    await grantPermission({
      grantee_type: permission.grantee_type,
      grantee_id: permission.grantee_id,
      resource_type: permission.resource_type,
      resource_id: permission.resource_id,
      permission: permission.permission,
      effect: permission.effect,
      inherit: true,
      expires_at: newExpiry.toISOString()
    })

    // Reload permissions
    await loadPermissions()
    alert('Permission extended successfully!')
  } catch (err: any) {
    alert(`Failed to extend permission: ${err.response?.data?.detail || err.message}`)
  }
}

// Get icon for grantee type
const getGranteeIcon = (type: string) => {
  return type === 'user' ? '👤' : '👥'
}

// Get icon for resource type
const getResourceIcon = (type: string) => {
  const icons: Record<string, string> = {
    site: '🏭',
    plan: '📋',
    sensor: '📡',
    broker: '🔌',
    alarm: '🚨',
    alert: '⚠️',
    dashboard: '📊',
    group: '👥',
    user: '👤'
  }
  return icons[type] || '📦'
}

// Lifecycle
onMounted(() => {
  loadPermissions()
})
</script>

<template>
  <div class="bg-white shadow rounded-lg">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-2xl font-bold text-gray-900">Upcoming Expirations</h2>
          <p class="mt-1 text-sm text-gray-500">
            Monitor and manage permissions that are about to expire
          </p>
        </div>
        <button
          @click="loadPermissions"
          :disabled="loading"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>

      <!-- Filters -->
      <div class="mt-4 flex items-center gap-4">
        <div class="flex items-center gap-2">
          <label class="text-sm font-medium text-gray-700">Show:</label>
          <select
            v-model="daysFilter"
            @change="loadPermissions"
            class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option v-for="option in filterOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <label class="text-sm font-medium text-gray-700">Group by:</label>
          <select
            v-model="groupBy"
            class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="user">User/Group</option>
            <option value="resource">Resource</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="px-6 py-4 bg-red-50 border-b border-red-200">
      <p class="text-red-700">{{ error }}</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="px-6 py-12 text-center">
      <div class="text-gray-500">Loading expiring permissions...</div>
    </div>

    <!-- Empty State -->
    <div v-else-if="permissions.length === 0" class="px-6 py-12 text-center">
      <div class="text-gray-500">
        No permissions expiring in the next {{ daysFilter }} days
      </div>
    </div>

    <!-- Grouped by User/Group -->
    <div v-else-if="groupBy === 'user'" class="divide-y divide-gray-200">
      <div
        v-for="(perms, key) in groupedByGrantee"
        :key="key"
        class="px-6 py-4 hover:bg-gray-50"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3">
            <span class="text-2xl">{{ getGranteeIcon(perms[0].grantee_type) }}</span>
            <div>
              <h3 class="text-lg font-semibold text-gray-900">
                {{ perms[0].grantee_name || perms[0].grantee_id }}
              </h3>
              <p class="text-sm text-gray-500">
                {{ perms.length }} permission{{ perms.length !== 1 ? 's' : '' }} expiring
              </p>
            </div>
          </div>
        </div>

        <!-- Permissions list -->
        <div class="ml-11 space-y-2">
          <div
            v-for="perm in perms"
            :key="perm.id"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span>{{ getResourceIcon(perm.resource_type) }}</span>
                <span class="font-medium text-gray-900">
                  {{ perm.resource_name || perm.resource_id }}
                </span>
                <span
                  class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="{
                    'bg-purple-100 text-purple-800': perm.permission === 'manage',
                    'bg-blue-100 text-blue-800': perm.permission === 'read',
                    'bg-green-100 text-green-800': perm.permission === 'write',
                    'bg-orange-100 text-orange-800': perm.permission === 'create',
                    'bg-red-100 text-red-800': perm.permission === 'delete'
                  }"
                >
                  {{ perm.permission }}
                </span>
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-600">
                <span>Expires: {{ formatDate(perm.expires_at) }}</span>
                <span
                  class="px-2 py-0.5 rounded-full border text-xs font-medium"
                  :class="getUrgencyBadge(perm.days_until_expiry)"
                >
                  {{ perm.days_until_expiry }} day{{ perm.days_until_expiry !== 1 ? 's' : '' }} left
                </span>
              </div>
            </div>
            <button
              @click="extendExpiration(perm)"
              class="ml-4 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              title="Extend by 30 days"
            >
              Extend
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Grouped by Resource -->
    <div v-else class="divide-y divide-gray-200">
      <div
        v-for="(perms, key) in groupedByResource"
        :key="key"
        class="px-6 py-4 hover:bg-gray-50"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3">
            <span class="text-2xl">{{ getResourceIcon(perms[0].resource_type) }}</span>
            <div>
              <h3 class="text-lg font-semibold text-gray-900">
                {{ perms[0].resource_name || perms[0].resource_id }}
              </h3>
              <p class="text-sm text-gray-500">
                {{ perms[0].resource_type }} • {{ perms.length }} permission{{ perms.length !== 1 ? 's' : '' }} expiring
              </p>
            </div>
          </div>
        </div>

        <!-- Permissions list -->
        <div class="ml-11 space-y-2">
          <div
            v-for="perm in perms"
            :key="perm.id"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span>{{ getGranteeIcon(perm.grantee_type) }}</span>
                <span class="font-medium text-gray-900">
                  {{ perm.grantee_name || perm.grantee_id }}
                </span>
                <span
                  class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="{
                    'bg-purple-100 text-purple-800': perm.permission === 'manage',
                    'bg-blue-100 text-blue-800': perm.permission === 'read',
                    'bg-green-100 text-green-800': perm.permission === 'write',
                    'bg-orange-100 text-orange-800': perm.permission === 'create',
                    'bg-red-100 text-red-800': perm.permission === 'delete'
                  }"
                >
                  {{ perm.permission }}
                </span>
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-600">
                <span>Expires: {{ formatDate(perm.expires_at) }}</span>
                <span
                  class="px-2 py-0.5 rounded-full border text-xs font-medium"
                  :class="getUrgencyBadge(perm.days_until_expiry)"
                >
                  {{ perm.days_until_expiry }} day{{ perm.days_until_expiry !== 1 ? 's' : '' }} left
                </span>
              </div>
            </div>
            <button
              @click="extendExpiration(perm)"
              class="ml-4 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              title="Extend by 30 days"
            >
              Extend
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Summary Footer -->
    <div v-if="permissions.length > 0" class="px-6 py-4 bg-gray-50 border-t border-gray-200">
      <div class="flex items-center justify-between text-sm">
        <span class="text-gray-600">
          Total: {{ permissions.length }} permission{{ permissions.length !== 1 ? 's' : '' }} expiring
        </span>
        <div class="flex gap-4">
          <span class="text-red-600">
            {{ permissions.filter(p => p.days_until_expiry <= 1).length }} urgent
          </span>
          <span class="text-orange-600">
            {{ permissions.filter(p => p.days_until_expiry > 1 && p.days_until_expiry <= 3).length }} soon
          </span>
          <span class="text-yellow-600">
            {{ permissions.filter(p => p.days_until_expiry > 3 && p.days_until_expiry <= 7).length }} this week
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
