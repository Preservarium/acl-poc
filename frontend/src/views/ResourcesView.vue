<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import ResourceTree from '@/components/ResourceTree.vue'
import PermissionManager from '@/components/PermissionManager.vue'
import { createSite, createPlan, createSensor } from '@/api/resources'

const authStore = useAuthStore()
const userIsAdmin = computed(() => authStore.user?.is_admin || false)

// Permission Manager Modal State
const showPermissionManager = ref(false)
const selectedResource = ref({
  type: '',
  id: '',
  name: ''
})

// Create Resource Modal State
const showCreateModal = ref(false)
const createModalType = ref<'site' | 'plan' | 'sensor'>('site')
const createForm = ref({
  name: '',
  site_id: '',
  plan_id: ''
})
const creating = ref(false)
const createError = ref<string | null>(null)

// Reference to ResourceTree component
const resourceTreeRef = ref<InstanceType<typeof ResourceTree> | null>(null)

const handleManagePermissions = (type: string, id: string, name: string) => {
  selectedResource.value = { type, id, name }
  showPermissionManager.value = true
}

const handleEditResource = (type: string, id: string) => {
  // TODO: Implement edit functionality
  console.log('Edit resource:', type, id)
}

const handleCreateSite = () => {
  createModalType.value = 'site'
  createForm.value = { name: '', site_id: '', plan_id: '' }
  createError.value = null
  showCreateModal.value = true
}

const handleCloseCreateModal = () => {
  showCreateModal.value = false
  createForm.value = { name: '', site_id: '', plan_id: '' }
  createError.value = null
}

const handleSubmitCreate = async () => {
  if (!createForm.value.name.trim()) {
    createError.value = 'Name is required'
    return
  }

  creating.value = true
  createError.value = null

  try {
    if (createModalType.value === 'site') {
      await createSite({ name: createForm.value.name })
    } else if (createModalType.value === 'plan') {
      await createPlan({ name: createForm.value.name, site_id: createForm.value.site_id })
    } else if (createModalType.value === 'sensor') {
      await createSensor({ name: createForm.value.name, plan_id: createForm.value.plan_id })
    }

    // Reload tree
    if (resourceTreeRef.value) {
      await resourceTreeRef.value.loadData()
    }

    handleCloseCreateModal()
  } catch (err: any) {
    createError.value = err.response?.data?.detail || 'Failed to create resource'
  } finally {
    creating.value = false
  }
}

const handlePermissionsUpdated = async () => {
  // Optionally reload tree if permissions affect visibility
  if (resourceTreeRef.value) {
    await resourceTreeRef.value.loadData()
  }
}
</script>

<template>
  <AppLayout>
  <div class="container mx-auto px-4 py-8">
    <ResourceTree
      ref="resourceTreeRef"
      :user-is-admin="userIsAdmin"
      @manage-permissions="handleManagePermissions"
      @edit-resource="handleEditResource"
      @create-site="handleCreateSite"
    />

    <!-- Permission Manager Modal -->
    <PermissionManager
      :show="showPermissionManager"
      :resource-type="selectedResource.type"
      :resource-id="selectedResource.id"
      :resource-name="selectedResource.name"
      @close="showPermissionManager = false"
      @updated="handlePermissionsUpdated"
    />

    <!-- Create Resource Modal -->
    <Transition name="modal">
      <div
        v-if="showCreateModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
        @click.self="handleCloseCreateModal"
      >
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
          <!-- Header -->
          <div class="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 class="text-xl font-bold text-gray-800">
              Create New {{ createModalType.charAt(0).toUpperCase() + createModalType.slice(1) }}
            </h2>
            <button
              @click="handleCloseCreateModal"
              class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
            >
              ×
            </button>
          </div>

          <!-- Content -->
          <div class="p-6">
            <!-- Error Message -->
            <div v-if="createError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {{ createError }}
            </div>

            <form @submit.prevent="handleSubmitCreate" class="space-y-4">
              <!-- Name Field -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  v-model="createForm.name"
                  type="text"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter name"
                />
              </div>

              <!-- Buttons -->
              <div class="flex justify-end gap-3">
                <button
                  type="button"
                  @click="handleCloseCreateModal"
                  class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  :disabled="creating"
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {{ creating ? 'Creating...' : 'Create' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Transition>
  </div>
  </AppLayout>
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
