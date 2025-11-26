<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { fetchUserEffectivePermissions } from '@/api/users'
import type { EffectivePermissionsResponse } from '@/types'
import { useAuthStore } from '@/stores/auth'

interface Props {
  userId?: string
}

const props = defineProps<Props>()
const authStore = useAuthStore()

const permissions = ref<EffectivePermissionsResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const currentUserId = computed(() => props.userId || authStore.user?.id || '')

const loadPermissions = async () => {
  if (!currentUserId.value) return

  loading.value = true
  error.value = null
  try {
    permissions.value = await fetchUserEffectivePermissions(currentUserId.value)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load effective permissions'
  } finally {
    loading.value = false
  }
}

const getResourceIcon = (type: string) => {
  switch (type) {
    case 'site': return '🏭'
    case 'plan': return '📋'
    case 'sensor': return '📡'
    case 'broker': return '📶'
    case 'alarm': return '🔔'
    case 'alert': return '⚠️'
    case 'dashboard': return '📊'
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
  <div class="effective-permissions">
    <!-- Header -->
    <div class="mb-6 pb-4 border-b border-gray-200">
      <div class="flex justify-between items-center">
        <h2 class="text-2xl font-bold text-gray-800">
          EFFECTIVE PERMISSIONS FOR:
          <span class="text-blue-600">{{ permissions?.user.username || '...' }}</span>
        </h2>
        <button
          @click="loadPermissions"
          class="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
        >
          🔄 Refresh
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12 text-gray-500">
      Loading effective permissions...
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
    <div v-else-if="permissions" class="space-y-6">
      <!-- Sites Administered -->
      <section v-if="permissions.sites_administered.length > 0" class="permission-group">
        <h3 class="text-lg font-semibold text-gray-700 mb-3">
          📍 SITES ADMINISTERED (manage permission)
        </h3>
        <div class="bg-white border border-gray-200 rounded-lg p-4 space-y-2">
          <div
            v-for="site in permissions.sites_administered"
            :key="site.resource_id"
            class="flex items-center justify-between py-2 px-3 hover:bg-gray-50 rounded"
          >
            <div class="flex items-center gap-2">
              <span class="text-xl">🏭</span>
              <router-link
                :to="`/sites/${site.resource_id}`"
                class="text-blue-600 hover:underline font-medium"
              >
                {{ site.resource_name }}
              </router-link>
            </div>
            <span class="text-sm text-gray-600">via: {{ site.source }}</span>
          </div>
        </div>
      </section>

      <!-- Sites with Write Access -->
      <section v-if="permissions.sites_write.length > 0" class="permission-group">
        <h3 class="text-lg font-semibold text-gray-700 mb-3">
          📍 SITES WITH WRITE ACCESS
        </h3>
        <div class="bg-white border border-gray-200 rounded-lg p-4 space-y-2">
          <div
            v-for="site in permissions.sites_write"
            :key="site.resource_id"
            class="flex items-center justify-between py-2 px-3 hover:bg-gray-50 rounded"
          >
            <div class="flex items-center gap-2">
              <span class="text-xl">🏭</span>
              <router-link
                :to="`/sites/${site.resource_id}`"
                class="text-blue-600 hover:underline font-medium"
              >
                {{ site.resource_name }}
              </router-link>
            </div>
            <span class="text-sm text-gray-600">via: {{ site.source }}</span>
          </div>
        </div>
      </section>

      <!-- Sites with Read Access -->
      <section v-if="permissions.sites_read.length > 0" class="permission-group">
        <h3 class="text-lg font-semibold text-gray-700 mb-3">
          📍 SITES WITH READ ACCESS
        </h3>
        <div class="bg-white border border-gray-200 rounded-lg p-4 space-y-2">
          <div
            v-for="site in permissions.sites_read"
            :key="site.resource_id"
            class="flex items-center justify-between py-2 px-3 hover:bg-gray-50 rounded"
          >
            <div class="flex items-center gap-2">
              <span class="text-xl">🏭</span>
              <router-link
                :to="`/sites/${site.resource_id}`"
                class="text-blue-600 hover:underline font-medium"
              >
                {{ site.resource_name }}
              </router-link>
            </div>
            <span class="text-sm text-gray-600">via: {{ site.source }}</span>
          </div>
        </div>
      </section>

      <!-- Direct Permissions -->
      <section v-if="permissions.direct_permissions.length > 0" class="permission-group">
        <h3 class="text-lg font-semibold text-gray-700 mb-3">
          📍 DIRECT PERMISSIONS (granted to user, not via group)
        </h3>
        <div class="bg-white border border-gray-200 rounded-lg p-4 space-y-2">
          <div
            v-for="perm in permissions.direct_permissions"
            :key="`${perm.resource_type}-${perm.resource_id}`"
            class="flex items-center justify-between py-2 px-3 hover:bg-gray-50 rounded"
          >
            <div class="flex items-center gap-3">
              <span class="text-xl">{{ getResourceIcon(perm.resource_type) }}</span>
              <span class="font-mono text-sm text-gray-600">
                {{ perm.resource_type }}:{{ perm.resource_name }}
              </span>
              <span
                class="px-2 py-1 text-xs font-semibold rounded-full"
                :class="getPermissionColor(perm.permission)"
              >
                {{ perm.permission }}
              </span>
            </div>
            <span class="text-sm text-gray-600">({{ perm.source }})</span>
          </div>
        </div>
      </section>

      <!-- Group Memberships -->
      <section v-if="permissions.groups.length > 0" class="permission-group">
        <h3 class="text-lg font-semibold text-gray-700 mb-3">
          📍 GROUP MEMBERSHIPS
        </h3>
        <div class="bg-white border border-gray-200 rounded-lg p-4 space-y-2">
          <div
            v-for="group in permissions.groups"
            :key="group.id"
            class="flex items-center gap-2 py-2 px-3 hover:bg-gray-50 rounded"
          >
            <span class="text-xl">👥</span>
            <router-link
              :to="`/groups/${group.id}`"
              class="text-blue-600 hover:underline font-medium"
            >
              {{ group.name }}
            </router-link>
          </div>
        </div>
      </section>

      <!-- Empty State -->
      <div
        v-if="permissions.sites_administered.length === 0 &&
              permissions.sites_write.length === 0 &&
              permissions.sites_read.length === 0 &&
              permissions.direct_permissions.length === 0 &&
              permissions.groups.length === 0"
        class="text-center py-12 text-gray-500 bg-gray-50 rounded-lg"
      >
        <p class="text-lg">No permissions found for this user</p>
        <p class="text-sm mt-2">The user has not been granted any permissions yet.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.permission-group {
  @apply mb-6;
}

.resource-item {
  @apply flex items-center justify-between p-3 hover:bg-gray-50 rounded transition-colors;
}
</style>
