<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { fetchUsers, fetchGroups } from '@/api/users'
import { grantPermission } from '@/api/permissions'
import FieldSelector from './permissions/FieldSelector.vue'
import type { User, Group, GranteeType, PermissionType } from '@/types'

const props = defineProps<{
  resourceType: string
  resourceId: string
}>()

const emit = defineEmits<{
  'granted': []
}>()

const granteeType = ref<GranteeType>('user')
const granteeId = ref('')
const permission = ref<PermissionType>('read')
const inherit = ref(true)
const expiresAt = ref<string>('')
const selectedFields = ref<string[] | null>(null)

const users = ref<User[]>([])
const groups = ref<Group[]>([])
const loading = ref(false)
const submitting = ref(false)
const error = ref<string | null>(null)

const loadGrantees = async () => {
  loading.value = true
  error.value = null
  try {
    const [usersData, groupsData] = await Promise.all([
      fetchUsers(),
      fetchGroups()
    ])
    users.value = usersData
    groups.value = groupsData
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load users and groups'
  } finally {
    loading.value = false
  }
}

// Reset grantee selection when type changes
watch(granteeType, () => {
  granteeId.value = ''
})

const granteeOptions = ref<Array<{ id: string; name: string }>>([])

watch([granteeType, users, groups], () => {
  if (granteeType.value === 'user') {
    granteeOptions.value = users.value.map(u => ({ id: u.id, name: u.username }))
  } else {
    granteeOptions.value = groups.value.map(g => ({ id: g.id, name: g.name }))
  }
}, { immediate: true })

// Available fields based on resource type
const availableFields = computed(() => {
  switch (props.resourceType) {
    case 'site':
      return ['name', 'created_by', 'created_at']
    case 'plan':
      return ['name', 'site_id', 'created_by', 'created_at']
    case 'sensor':
      return ['name', 'plan_id', 'created_by', 'created_at']
    case 'alarm':
      return ['name', 'sensor_id', 'created_by', 'created_at']
    case 'alert':
      return ['message', 'severity', 'alarm_id', 'created_by', 'created_at']
    case 'broker':
      return ['name', 'protocol', 'plan_id', 'created_by', 'created_at']
    case 'dashboard':
      return ['name', 'config', 'created_by', 'created_at']
    case 'group':
      return ['name', 'created_at']
    default:
      return []
  }
})

const handleSubmit = async () => {
  if (!granteeId.value) {
    error.value = 'Please select a grantee'
    return
  }

  submitting.value = true
  error.value = null

  try {
    const grantData: any = {
      grantee_type: granteeType.value,
      grantee_id: granteeId.value,
      resource_type: props.resourceType as any,
      resource_id: props.resourceId,
      permission: permission.value,
      effect: 'allow',
      inherit: inherit.value
    }

    // Add optional fields if they have values
    if (expiresAt.value) {
      grantData.expires_at = expiresAt.value
    }

    if (selectedFields.value && selectedFields.value.length > 0) {
      grantData.fields = selectedFields.value
    }

    await grantPermission(grantData)

    // Reset form
    granteeId.value = ''
    permission.value = 'read'
    inherit.value = true
    expiresAt.value = ''
    selectedFields.value = null

    emit('granted')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to grant permission'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadGrantees()
})
</script>

<template>
  <div class="border rounded-lg p-4 bg-gray-50">
    <h3 class="text-lg font-semibold text-gray-800 mb-4">Grant New Permission</h3>

    <!-- Error Message -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-4 text-gray-500">
      Loading...
    </div>

    <!-- Form -->
    <form v-else @submit.prevent="handleSubmit" class="space-y-4">
      <!-- Type Selection -->
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Type
          </label>
          <select
            v-model="granteeType"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="user">User</option>
            <option value="group">Group</option>
          </select>
        </div>

        <!-- Grantee Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Grantee
          </label>
          <select
            v-model="granteeId"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="" disabled>Select...</option>
            <option v-for="option in granteeOptions" :key="option.id" :value="option.id">
              {{ option.name }}
            </option>
          </select>
        </div>
      </div>

      <!-- Permission Selection -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Permission
        </label>
        <select
          v-model="permission"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="read">Read</option>
          <option value="write">Write</option>
          <option value="delete">Delete</option>
          <option value="create">Create</option>
          <option value="manage">Manage</option>
          <option value="member">Member</option>
        </select>
      </div>

      <!-- Field Selector -->
      <FieldSelector
        v-if="permission === 'read' || permission === 'write'"
        :available-fields="availableFields"
        v-model="selectedFields"
      />

      <!-- Expiration Date -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Expiration Date (optional)
        </label>
        <input
          v-model="expiresAt"
          type="datetime-local"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Leave empty for no expiration"
        />
        <p class="text-xs text-gray-500 mt-1">
          Permission will be automatically revoked after this date/time
        </p>
      </div>

      <!-- Inherit Checkbox -->
      <div class="flex items-center gap-2">
        <input
          v-model="inherit"
          type="checkbox"
          id="inherit-checkbox"
          class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        <label for="inherit-checkbox" class="text-sm font-medium text-gray-700">
          Inherit to children
        </label>
      </div>

      <!-- Submit Button -->
      <div class="flex justify-end">
        <button
          type="submit"
          :disabled="submitting || !granteeId"
          class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <span>+</span>
          <span>{{ submitting ? 'Granting...' : 'Grant' }}</span>
        </button>
      </div>
    </form>
  </div>
</template>
