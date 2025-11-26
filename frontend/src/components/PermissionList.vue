<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Permission } from '@/types'

const props = defineProps<{
  permissions: Permission[]
  loading?: boolean
}>()

const emit = defineEmits<{
  'revoke': [permissionId: string]
}>()

const getIcon = (granteeType: string) => {
  return granteeType === 'user' ? '👤' : '👥'
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}
</script>

<template>
  <div class="border rounded-lg overflow-hidden">
    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8 text-gray-500">
      Loading permissions...
    </div>

    <!-- Empty State -->
    <div v-else-if="permissions.length === 0" class="text-center py-8 text-gray-500">
      No permissions set for this resource
    </div>

    <!-- Permissions Table -->
    <table v-else class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Grantee
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Permission
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Effect
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Inherit
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Fields
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Granted
          </th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
            Expires
          </th>
          <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
            Actions
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">
        <tr v-for="permission in permissions" :key="permission.id" class="hover:bg-gray-50">
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center gap-2">
              <span class="text-lg">{{ getIcon(permission.grantee_type) }}</span>
              <span class="text-sm font-medium text-gray-900">
                {{ permission.grantee_name || permission.grantee_id }}
              </span>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="{
                    'bg-purple-100 text-purple-800': permission.permission === 'manage',
                    'bg-blue-100 text-blue-800': permission.permission === 'read',
                    'bg-green-100 text-green-800': permission.permission === 'write',
                    'bg-orange-100 text-orange-800': permission.permission === 'create',
                    'bg-red-100 text-red-800': permission.permission === 'delete',
                    'bg-indigo-100 text-indigo-800': permission.permission === 'member'
                  }">
              {{ permission.permission }}
            </span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="{
                    'bg-green-100 text-green-800': permission.effect === 'allow',
                    'bg-red-100 text-red-800': permission.effect === 'deny'
                  }">
              {{ permission.effect }}
            </span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-center">
            <span v-if="permission.inherit" class="text-green-600 text-lg">✓</span>
            <span v-else class="text-gray-300 text-lg">−</span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            <span v-if="permission.fields && permission.fields.length > 0" class="text-xs">
              {{ permission.fields.join(', ') }}
            </span>
            <span v-else class="text-gray-400">All</span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            {{ formatDate(permission.granted_at) }}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            <span v-if="permission.expires_at" class="text-xs">
              {{ formatDate(permission.expires_at) }}
            </span>
            <span v-else class="text-gray-400">Never</span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right">
            <button
              @click="emit('revoke', permission.id)"
              class="text-red-600 hover:text-red-800 transition-colors"
              title="Revoke permission"
            >
              🗑️
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
