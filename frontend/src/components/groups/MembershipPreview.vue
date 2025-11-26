<script setup lang="ts">
import { computed } from 'vue'
import type { Permission } from '@/types'

interface Props {
  permissions: Permission[]
}

const props = defineProps<Props>()

const getResourceIcon = (type: string) => {
  switch (type) {
    case 'site': return '🏭'
    case 'plan': return '📋'
    case 'sensor': return '📡'
    case 'alarm': return '🔔'
    case 'alert': return '⚠️'
    case 'broker': return '🔌'
    case 'group': return '👥'
    default: return '📄'
  }
}

const getPermissionDescription = (permission: string) => {
  switch (permission) {
    case 'manage':
      return 'Full control over the resource and all children'
    case 'write':
      return 'Can modify the resource'
    case 'read':
      return 'Can view the resource'
    case 'create':
      return 'Can create child resources'
    case 'delete':
      return 'Can delete the resource'
    default:
      return 'Access to the resource'
  }
}

// Group permissions by resource
const groupedPermissions = computed(() => {
  const grouped = new Map<string, Permission>()

  // Group by resource_id and keep the highest permission
  props.permissions.forEach(perm => {
    const key = `${perm.resource_type}:${perm.resource_id}`
    const existing = grouped.get(key)

    if (!existing || getPermissionPriority(perm.permission) > getPermissionPriority(existing.permission)) {
      grouped.set(key, perm)
    }
  })

  return Array.from(grouped.values())
})

const getPermissionPriority = (permission: string): number => {
  const priorities: Record<string, number> = {
    'manage': 5,
    'delete': 4,
    'write': 3,
    'create': 2,
    'read': 1
  }
  return priorities[permission] || 0
}
</script>

<template>
  <div class="membership-preview">
    <div v-if="groupedPermissions.length === 0" class="empty-state">
      <p class="text-gray-500 text-sm">This group has no permissions assigned yet.</p>
    </div>

    <div v-else class="permissions-list">
      <div
        v-for="perm in groupedPermissions"
        :key="`${perm.resource_type}:${perm.resource_id}`"
        class="permission-item"
      >
        <div class="permission-header">
          <span class="resource-icon">{{ getResourceIcon(perm.resource_type) }}</span>
          <span class="permission-level">{{ perm.permission }}</span>
          <span class="text-gray-600">on</span>
          <span class="resource-name">
            {{ perm.resource_type }}:{{ perm.resource_name || perm.resource_id }}
          </span>
          <span v-if="perm.inherit" class="inherit-badge">(inherited)</span>
        </div>
        <div class="permission-description">
          {{ getPermissionDescription(perm.permission) }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.membership-preview {
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  padding: 0.75rem;
  margin-bottom: 1rem;
}

.empty-state {
  padding: 0.5rem;
  text-align: center;
}

.permissions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.permission-item {
  border-left: 3px solid #3b82f6;
  padding-left: 0.75rem;
}

.permission-header {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.resource-icon {
  font-size: 1rem;
}

.permission-level {
  font-weight: 600;
  color: #1f2937;
  text-transform: uppercase;
  font-size: 0.75rem;
  background-color: #dbeafe;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  color: #1e40af;
}

.resource-name {
  font-weight: 500;
  color: #374151;
  font-family: monospace;
  font-size: 0.8125rem;
}

.inherit-badge {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
}

.permission-description {
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.4;
}
</style>
