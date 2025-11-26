<template>
  <AppLayout>
    <div class="max-w-2xl mx-auto py-8">
      <div class="bg-white shadow-sm rounded-lg border border-gray-200 p-8">
        <!-- Header with icon -->
        <div class="text-center mb-6">
          <div class="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
            <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <p class="text-gray-600">{{ detailMessage }}</p>
        </div>

        <!-- Permissions Section -->
        <div v-if="permissionDetails" class="mb-6">
          <h2 class="text-sm font-semibold text-gray-700 mb-3">Your permissions on this resource:</h2>
          <div class="bg-gray-50 rounded-md border border-gray-200 p-4 space-y-2">
            <div
              v-for="perm in sortedPermissions"
              :key="perm.permission"
              class="flex items-center justify-between py-2"
            >
              <div class="flex items-center space-x-3">
                <span v-if="perm.allowed" class="text-green-500 font-medium">✓</span>
                <span v-else class="text-red-500 font-medium">✗</span>
                <span class="font-medium text-gray-900">{{ perm.permission }}</span>
                <span v-if="perm.via && perm.allowed" class="text-sm text-gray-500">
                  (via {{ perm.via_type === 'group' ? perm.via : 'direct permission' }})
                </span>
              </div>
              <span
                v-if="!perm.allowed && perm.permission === permissionDetails.required_permission"
                class="text-sm font-medium text-red-600"
              >
                ← Required
              </span>
            </div>
          </div>
        </div>

        <!-- Help Text -->
        <div class="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
          <p class="text-sm text-blue-900">
            Contact an administrator if you need additional access to this resource.
          </p>
        </div>

        <!-- Action Button -->
        <div class="flex justify-center">
          <button
            @click="goBack"
            class="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { PermissionDeniedDetail, PermissionSource } from '@/types'
import AppLayout from '@/components/AppLayout.vue'

const route = useRoute()
const router = useRouter()

const permissionDetails = ref<PermissionDeniedDetail | null>(null)

const detailMessage = computed(() => {
  if (permissionDetails.value) {
    return permissionDetails.value.detail
  }
  return "You don't have permission to access this resource."
})

const sortedPermissions = computed(() => {
  if (!permissionDetails.value) return []

  const perms = [...permissionDetails.value.user_permissions]

  // Sort: required permission first, then allowed permissions, then denied
  return perms.sort((a, b) => {
    // Required permission comes first
    if (a.permission === permissionDetails.value?.required_permission) return -1
    if (b.permission === permissionDetails.value?.required_permission) return 1

    // Then sort by allowed status (allowed first)
    if (a.allowed !== b.allowed) return a.allowed ? -1 : 1

    // Then alphabetically
    return a.permission.localeCompare(b.permission)
  })
})

onMounted(() => {
  // Try to get permission details from route state
  const state = router.options.history.state as any
  if (state && state.permissionDetails) {
    permissionDetails.value = state.permissionDetails
  } else {
    // Fallback: construct from query params if available
    const resourceType = route.query.resource_type as string
    const resourceId = route.query.resource_id as string
    const action = route.query.action as string

    if (resourceType && resourceId && action) {
      permissionDetails.value = {
        detail: `You don't have permission to ${action} this ${resourceType}.`,
        required_permission: action as any,
        resource_type: resourceType as any,
        resource_id: resourceId,
        user_permissions: []
      }
    }
  }
})

const goBack = () => {
  router.back()
}
</script>
