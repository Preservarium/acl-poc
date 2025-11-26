<script setup lang="ts">
import type { EffectivePermission } from '@/types'

interface Props {
  permissions: EffectivePermission[]
}

defineProps<Props>()

const formatPermissions = (permissions: string[], fields?: string[]) => {
  const permStr = permissions.join(', ')
  if (fields && fields.length > 0) {
    return `${permStr} (${fields.join(', ')})`
  }
  return `${permStr} (all)`
}
</script>

<template>
  <div class="effective-access-list">
    <div v-if="permissions.length === 0" class="empty-state">
      No effective permissions
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="perm in permissions"
        :key="perm.user_id"
        class="effective-row"
      >
        <div class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
          <span class="text-xl flex-shrink-0">👤</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-baseline gap-2 flex-wrap">
              <span class="font-medium text-gray-900">{{ perm.username }}</span>
              <span class="text-sm text-gray-600">
                {{ formatPermissions(perm.permissions, perm.fields) }}
              </span>
            </div>
            <div class="text-xs text-gray-500 mt-1">
              via {{ perm.sources.join(' + ') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.effective-row {
  transition: all 0.2s ease;
}

.effective-row:hover {
  transform: translateX(2px);
}
</style>
