<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { fetchGroups } from '@/api/users'
import AppLayout from '@/components/AppLayout.vue'
import type { Group } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

const groups = ref<Group[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const showCreateModal = ref(false)
const newGroup = ref({
  name: '',
  description: ''
})

const isAdmin = computed(() => authStore.user?.is_admin || false)

// Computed property for filtered groups based on search
const filteredGroups = computed(() => {
  if (!searchQuery.value) {
    return groups.value
  }
  const query = searchQuery.value.toLowerCase()
  return groups.value.filter(group =>
    group.name.toLowerCase().includes(query)
  )
})

const loadGroups = async () => {
  loading.value = true
  error.value = null

  try {
    const groupsData = await fetchGroups()
    groups.value = groupsData
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load groups'
  } finally {
    loading.value = false
  }
}

const viewGroup = (group: Group) => {
  router.push(`/groups/${group.id}`)
}

const createGroup = async () => {
  if (!newGroup.value.name.trim()) {
    return
  }

  try {
    // TODO: Implement createGroup API call
    // await createGroupAPI(newGroup.value)

    // For now, just close the modal and refresh
    showCreateModal.value = false
    newGroup.value = { name: '', description: '' }
    await loadGroups()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to create group'
  }
}

onMounted(() => {
  loadGroups()
})
</script>

<template>
  <AppLayout>
    <div class="p-6">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">👥 Groups</h1>
        <button
          v-if="isAdmin"
          @click="showCreateModal = true"
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
        >
          + Create Group
        </button>
      </div>

      <!-- Search -->
      <div class="mb-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="🔍 Search groups..."
          class="w-full md:w-96 px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <!-- Error State -->
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-center">
        <p class="text-red-700 mb-2">{{ error }}</p>
        <button
          @click="loadGroups"
          class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Groups List -->
      <div class="bg-white rounded-lg shadow">
        <!-- Table header -->
        <div class="grid grid-cols-12 gap-4 p-4 border-b font-semibold text-gray-600 text-sm">
          <div class="col-span-5">GROUP NAME</div>
          <div class="col-span-2 text-center">MEMBERS</div>
          <div class="col-span-4">PERMISSIONS</div>
          <div class="col-span-1">ACTIONS</div>
        </div>

        <!-- Loading state -->
        <div v-if="loading" class="p-8 text-center text-gray-500">
          Loading groups...
        </div>

        <!-- Empty state -->
        <div v-else-if="filteredGroups.length === 0" class="p-8 text-center text-gray-500">
          <p v-if="searchQuery">No groups found matching "{{ searchQuery }}"</p>
          <p v-else>No groups found.</p>
        </div>

        <!-- Groups rows -->
        <div
          v-for="group in filteredGroups"
          :key="group.id"
          class="grid grid-cols-12 gap-4 p-4 border-b hover:bg-gray-50 items-start transition-colors"
        >
          <!-- Name -->
          <div class="col-span-5">
            <router-link
              :to="`/groups/${group.id}`"
              class="flex items-center text-blue-600 hover:underline font-medium"
            >
              👥 {{ group.name }}
            </router-link>
          </div>

          <!-- Members count -->
          <div class="col-span-2 text-center">
            <span class="bg-gray-100 px-3 py-1 rounded text-sm font-medium">
              -
            </span>
          </div>

          <!-- Permissions summary -->
          <div class="col-span-4">
            <span class="text-gray-600 text-sm">
              View details for permissions
            </span>
          </div>

          <!-- Actions -->
          <div class="col-span-1 text-center">
            <button
              @click="viewGroup(group)"
              class="text-gray-400 hover:text-gray-600 text-xl transition-colors"
              title="View group details"
            >
              ⋮
            </button>
          </div>
        </div>
      </div>

      <!-- Create Group Modal -->
      <div
        v-if="showCreateModal"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="showCreateModal = false"
      >
        <div class="bg-white rounded-lg p-6 w-96 shadow-xl">
          <h2 class="text-xl font-bold mb-4">Create Group</h2>

          <div class="mb-4">
            <label class="block text-sm font-medium mb-1 text-gray-700">Name</label>
            <input
              v-model="newGroup.name"
              type="text"
              class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter group name"
              @keyup.enter="createGroup"
            />
          </div>

          <div class="mb-6">
            <label class="block text-sm font-medium mb-1 text-gray-700">Description</label>
            <textarea
              v-model="newGroup.description"
              class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              placeholder="Optional description"
            ></textarea>
          </div>

          <div class="flex justify-end space-x-2">
            <button
              @click="showCreateModal = false"
              class="px-4 py-2 border rounded hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              @click="createGroup"
              class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              :disabled="!newGroup.name.trim()"
              :class="{ 'opacity-50 cursor-not-allowed': !newGroup.name.trim() }"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
