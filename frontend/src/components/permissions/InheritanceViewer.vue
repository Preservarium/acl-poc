<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import apiClient from '@/api/client'
import InheritanceNode from './InheritanceNode.vue'

interface User {
  id: string
  username: string
}

interface Group {
  id: string
  name: string
}

interface Permission {
  permission: string
  effect: string
  fields?: string[] | null
  source: string
  is_inherited: boolean
  depth: number
}

interface TreeNode {
  id: string
  name: string
  type: string
  permissions: Permission[]
  denies: Permission[]
  children: TreeNode[]
}

interface InheritanceData {
  user: User
  groups: Group[]
  tree: TreeNode[]
}

const selectedUserId = ref<string | null>(null)
const users = ref<User[]>([])
const inheritanceData = ref<InheritanceData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Load all users for the dropdown
const loadUsers = async () => {
  try {
    const response = await apiClient.get<User[]>('/users')
    users.value = response.data

    // Auto-select current user if available
    if (users.value.length > 0 && !selectedUserId.value) {
      // Try to get current user from localStorage or first user
      const currentUser = localStorage.getItem('username')
      const user = users.value.find(u => u.username === currentUser) || users.value[0]
      selectedUserId.value = user.id
    }
  } catch (err: any) {
    console.error('Failed to load users:', err)
  }
}

// Load inheritance tree for selected user
const loadInheritance = async () => {
  if (!selectedUserId.value) return

  loading.value = true
  error.value = null

  try {
    const response = await apiClient.get<InheritanceData>(
      `/permissions/user-inheritance/${selectedUserId.value}`
    )
    inheritanceData.value = response.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load inheritance data'
    inheritanceData.value = null
  } finally {
    loading.value = false
  }
}

// Watch for user selection changes
watch(selectedUserId, () => {
  if (selectedUserId.value) {
    loadInheritance()
  }
})

// Load users on mount
loadUsers()

const hasPermissions = computed(() => {
  return inheritanceData.value?.tree && inheritanceData.value.tree.length > 0
})
</script>

<template>
  <div class="inheritance-viewer border rounded-lg p-6 bg-white shadow-sm">
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-2xl font-bold mb-4">Permission Inheritance Viewer</h2>

      <!-- User Selector -->
      <div class="flex items-center gap-4 mb-4">
        <label for="user-select" class="font-medium text-gray-700">
          Select User:
        </label>
        <select
          id="user-select"
          v-model="selectedUserId"
          class="border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="" disabled>-- Select a user --</option>
          <option v-for="user in users" :key="user.id" :value="user.id">
            {{ user.username }}
          </option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8 text-gray-500">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mb-2"></div>
      <p>Loading inheritance data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-4 bg-red-50 border border-red-200 rounded text-red-700">
      {{ error }}
    </div>

    <!-- Content -->
    <div v-else-if="inheritanceData">
      <!-- User Info and Groups -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 class="text-lg font-semibold mb-3">
          Permission Inheritance Chain for:
          <span class="text-blue-700">{{ inheritanceData.user.username }}</span>
        </h3>

        <!-- Group Memberships -->
        <div v-if="inheritanceData.groups && inheritanceData.groups.length > 0">
          <p class="font-medium text-gray-700 mb-2">Group Memberships:</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="group in inheritanceData.groups"
              :key="group.id"
              class="inline-flex items-center bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
            >
              👥 {{ group.name }}
            </span>
          </div>
        </div>
        <div v-else class="text-gray-600 text-sm">
          No group memberships
        </div>
      </div>

      <!-- Permission Tree -->
      <div class="tree-container">
        <div v-if="hasPermissions" class="border rounded-lg overflow-hidden">
          <div class="bg-gray-50 px-4 py-2 border-b font-medium text-gray-700">
            Resource Hierarchy with Permissions
          </div>
          <div class="bg-white">
            <InheritanceNode
              v-for="node in inheritanceData.tree"
              :key="node.id"
              :node="node"
              :depth="0"
            />
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-12 text-gray-500">
          <p class="text-lg mb-2">No permissions found</p>
          <p class="text-sm">
            This user has no direct or inherited permissions on any resources.
          </p>
        </div>
      </div>

      <!-- Legend -->
      <div class="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 class="font-semibold text-gray-700 mb-3">Legend:</h4>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
          <div class="flex items-center gap-2">
            <span class="bg-purple-100 text-purple-800 px-2 py-1 rounded font-medium">manage</span>
            <span class="text-gray-600">Full control</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded font-medium">create</span>
            <span class="text-gray-600">Create resources</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="bg-green-100 text-green-800 px-2 py-1 rounded font-medium">write</span>
            <span class="text-gray-600">Modify data</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="bg-red-100 text-red-800 px-2 py-1 rounded font-medium">delete</span>
            <span class="text-gray-600">Delete resources</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="bg-gray-100 text-gray-800 px-2 py-1 rounded font-medium">read</span>
            <span class="text-gray-600">View only</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="bg-red-200 text-red-900 px-2 py-1 rounded font-bold">🚫 DENY</span>
            <span class="text-gray-600">Access blocked</span>
          </div>
        </div>
        <div class="mt-3 pt-3 border-t border-gray-200 text-sm text-gray-600">
          <p><strong>← inherited</strong> indicates permission is inherited from a parent resource</p>
          <p class="mt-1"><strong>via [Group Name]</strong> indicates permission comes from group membership</p>
        </div>
      </div>
    </div>

    <!-- No User Selected -->
    <div v-else class="text-center py-12 text-gray-500">
      <p class="text-lg">Select a user to view their permission inheritance tree</p>
    </div>
  </div>
</template>

<style scoped>
.tree-container {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
