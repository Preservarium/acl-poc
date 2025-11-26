<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import apiClient from '@/api/client'

const props = defineProps<{
  resourceType: string
  resourceId: string
}>()

interface EffectivePermissionDetail {
  permission: string
  effect: string
  fields: string[] | null
  inherit: boolean
  source: string
  depth: number
}

interface EffectivePermissionsResponse {
  user_id: string
  username: string
  resource_type: string
  resource_id: string
  resource_name: string
  permissions: EffectivePermissionDetail[]
}

const effectivePermissions = ref<EffectivePermissionsResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const loadEffectivePermissions = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await apiClient.get<EffectivePermissionsResponse>(
      `/permissions/resource/${props.resourceType}/${props.resourceId}/effective`
    )
    effectivePermissions.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load permissions'
  } finally {
    loading.value = false
  }
}

const permissionsList = computed(() => {
  if (!effectivePermissions.value) return []

  const permsMap = new Map<string, EffectivePermissionDetail[]>()

  effectivePermissions.value.permissions.forEach((perm) => {
    if (perm.effect === 'allow') {
      if (!permsMap.has(perm.permission)) {
        permsMap.set(perm.permission, [])
      }
      permsMap.get(perm.permission)!.push(perm)
    }
  })

  return Array.from(permsMap.entries()).map(([permission, details]) => {
    // Combine all fields from all sources
    const allFields: string[] = []
    let hasFullAccess = false

    details.forEach((detail) => {
      if (detail.fields === null) {
        hasFullAccess = true
      } else if (detail.fields) {
        allFields.push(...detail.fields)
      }
    })

    // Get most relevant source
    const primarySource = details.sort((a, b) => a.depth - b.depth)[0]

    return {
      permission,
      hasAccess: true,
      fields: hasFullAccess ? null : [...new Set(allFields)],
      source: primarySource.source,
      inherit: primarySource.inherit
    }
  })
})

const canRead = computed(() => {
  return permissionsList.value.some(p => p.permission === 'read' && p.hasAccess)
})

const canWrite = computed(() => {
  return permissionsList.value.some(p => p.permission === 'write' && p.hasAccess)
})

const canDelete = computed(() => {
  return permissionsList.value.some(p => p.permission === 'delete' && p.hasAccess)
})

const writePermission = computed(() => {
  return permissionsList.value.find(p => p.permission === 'write')
})

const formatSource = (source: string, inherit: boolean) => {
  // Format: "user:123 via site:456" or "group:789"
  // We want: "Group Name -> site:name (inherit)" or "Direct"

  const parts = source.split(' via ')
  const granteeInfo = parts[0]
  const resourceInfo = parts[1]

  let formatted = granteeInfo.startsWith('user:') ? 'Direct' : granteeInfo

  if (resourceInfo) {
    formatted += ` → ${resourceInfo}`
    if (inherit) {
      formatted += ' (inherit)'
    }
  }

  return formatted
}

onMounted(() => {
  loadEffectivePermissions()
})
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
    <div class="bg-gray-50 px-4 py-3 border-b border-gray-200">
      <h3 class="text-sm font-semibold text-gray-700 uppercase tracking-wide">
        Your Permissions on This {{ resourceType }}
      </h3>
    </div>

    <div class="p-4">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-4 text-gray-500 text-sm">
        Loading permissions...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-4">
        <p class="text-red-600 text-sm mb-2">{{ error }}</p>
        <button
          @click="loadEffectivePermissions"
          class="text-xs text-blue-600 hover:text-blue-700 underline"
        >
          Retry
        </button>
      </div>

      <!-- Permissions Display -->
      <div v-else-if="effectivePermissions">
        <!-- Permission Badges -->
        <div class="flex flex-wrap gap-3 mb-4">
          <!-- Read -->
          <div class="flex items-center gap-1.5">
            <span v-if="canRead" class="text-green-600 text-lg">✓</span>
            <span v-else class="text-red-500 text-lg">✗</span>
            <span class="text-sm font-medium" :class="canRead ? 'text-gray-700' : 'text-gray-400'">
              read
            </span>
          </div>

          <!-- Write -->
          <div class="flex items-center gap-1.5">
            <span v-if="canWrite" class="text-green-600 text-lg">✓</span>
            <span v-else class="text-red-500 text-lg">✗</span>
            <span class="text-sm font-medium" :class="canWrite ? 'text-gray-700' : 'text-gray-400'">
              write
              <span v-if="canWrite && writePermission?.fields" class="text-xs text-gray-500">
                (fields: {{ writePermission.fields.join(', ') }})
              </span>
            </span>
          </div>

          <!-- Delete -->
          <div class="flex items-center gap-1.5">
            <span v-if="canDelete" class="text-green-600 text-lg">✓</span>
            <span v-else class="text-red-500 text-lg">✗</span>
            <span class="text-sm font-medium" :class="canDelete ? 'text-gray-700' : 'text-gray-400'">
              delete
            </span>
          </div>
        </div>

        <!-- Source Attribution -->
        <div v-if="writePermission" class="mt-3 pt-3 border-t border-gray-200">
          <div class="text-xs text-gray-500">
            <span class="font-medium">Source:</span>
            <span class="ml-1">{{ formatSource(writePermission.source, writePermission.inherit) }}</span>
          </div>
        </div>

        <!-- No Permissions -->
        <div v-if="permissionsList.length === 0" class="text-center py-4 text-gray-500 text-sm">
          You have no permissions on this resource
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Ensure consistent spacing */
.flex-wrap {
  row-gap: 0.5rem;
}
</style>
