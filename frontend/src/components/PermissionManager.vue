<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { fetchResourcePermissions, revokePermission } from '@/api/permissions'
import PermissionList from './PermissionList.vue'
import PermissionGrant from './PermissionGrant.vue'
import type { Permission } from '@/types'

const props = defineProps<{
  show: boolean
  resourceType: string
  resourceId: string
  resourceName: string
}>()

const emit = defineEmits<{
  'close': []
  'updated': []
}>()

const permissions = ref<Permission[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const loadPermissions = async () => {
  if (!props.show || !props.resourceId) return

  loading.value = true
  error.value = null
  try {
    permissions.value = await fetchResourcePermissions(props.resourceType, props.resourceId)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load permissions'
  } finally {
    loading.value = false
  }
}

const handleRevoke = async (permissionId: string) => {
  if (!confirm('Are you sure you want to revoke this permission?')) {
    return
  }

  try {
    await revokePermission(permissionId)
    await loadPermissions()
    emit('updated')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to revoke permission'
  }
}

const handleGranted = async () => {
  await loadPermissions()
  emit('updated')
}

const getResourceIcon = (type: string) => {
  switch (type) {
    case 'site': return '🏭'
    case 'plan': return '📋'
    case 'sensor': return '📡'
    case 'alarm': return '🔔'
    case 'alert': return '⚠️'
    case 'broker': return '🔌'
    case 'dashboard': return '📊'
    default: return '📄'
  }
}

// Load permissions when modal opens
watch(() => props.show, (newShow) => {
  if (newShow) {
    loadPermissions()
  }
})

// Close modal on Escape key
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.show) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})
</script>

<template>
  <!-- Modal Backdrop -->
  <Transition name="modal">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      @click.self="emit('close')"
    >
      <!-- Modal Content -->
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200">
          <div class="flex items-center gap-2">
            <span class="text-2xl">{{ getResourceIcon(resourceType) }}</span>
            <h2 class="text-2xl font-bold text-gray-800">
              Permissions: {{ resourceName }}
            </h2>
          </div>
          <button
            @click="emit('close')"
            class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <!-- Error Message -->
          <div v-if="error" class="p-4 bg-red-50 border border-red-200 rounded text-red-700">
            {{ error }}
          </div>

          <!-- Current Permissions Section -->
          <div>
            <h3 class="text-lg font-semibold text-gray-800 mb-3">Current Permissions</h3>
            <PermissionList
              :permissions="permissions"
              :loading="loading"
              @revoke="handleRevoke"
            />
          </div>

          <!-- Grant Permission Section -->
          <PermissionGrant
            :resource-type="resourceType"
            :resource-id="resourceId"
            @granted="handleGranted"
          />
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.9);
}
</style>
