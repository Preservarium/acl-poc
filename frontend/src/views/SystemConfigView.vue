<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import axios from 'axios'

const authStore = useAuthStore()
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const isAdmin = computed(() => authStore.user?.is_admin || false)
const loading = ref(false)
const error = ref<string | null>(null)

// Active tab
const activeTab = ref<string>('hardware')

// Data for each config type
const hardware = ref<any[]>([])
const datatypes = ref<any[]>([])
const protocols = ref<any[]>([])
const parsers = ref<any[]>([])
const manufacturers = ref<any[]>([])
const communicationModes = ref<any[]>([])

// Modal state
const showModal = ref(false)
const modalMode = ref<'create' | 'edit'>('create')
const modalType = ref<string>('hardware')
const editingItem = ref<any>(null)
const formData = ref({
  name: '',
  description: ''
})

// Tab configuration
const tabs = [
  { id: 'hardware', label: 'Hardware', icon: '🖥️' },
  { id: 'datatypes', label: 'Data Types', icon: '📊' },
  { id: 'protocols', label: 'Protocols', icon: '🔌' },
  { id: 'parsers', label: 'Parsers', icon: '⚙️' },
  { id: 'manufacturers', label: 'Manufacturers', icon: '🏭' },
  { id: 'communication-modes', label: 'Communication Modes', icon: '📡' }
]

// Get current data based on active tab
const currentData = computed(() => {
  switch (activeTab.value) {
    case 'hardware': return hardware.value
    case 'datatypes': return datatypes.value
    case 'protocols': return protocols.value
    case 'parsers': return parsers.value
    case 'manufacturers': return manufacturers.value
    case 'communication-modes': return communicationModes.value
    default: return []
  }
})

// Get API endpoint for current tab
const getEndpoint = (type: string) => {
  return `${API_URL}/api/system-config/${type}`
}

// Load all data
const loadAllData = async () => {
  loading.value = true
  error.value = null

  try {
    const token = localStorage.getItem('token')
    const config = {
      headers: { Authorization: `Bearer ${token}` }
    }

    const [hwRes, dtRes, prRes, paRes, mfRes, cmRes] = await Promise.all([
      axios.get(getEndpoint('hardware'), config),
      axios.get(getEndpoint('datatypes'), config),
      axios.get(getEndpoint('protocols'), config),
      axios.get(getEndpoint('parsers'), config),
      axios.get(getEndpoint('manufacturers'), config),
      axios.get(getEndpoint('communication-modes'), config)
    ])

    hardware.value = hwRes.data
    datatypes.value = dtRes.data
    protocols.value = prRes.data
    parsers.value = paRes.data
    manufacturers.value = mfRes.data
    communicationModes.value = cmRes.data
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load system configuration'
    console.error('Error loading system config:', err)
  } finally {
    loading.value = false
  }
}

// Open create modal
const openCreateModal = () => {
  if (!isAdmin.value) return

  modalMode.value = 'create'
  modalType.value = activeTab.value
  formData.value = { name: '', description: '' }
  editingItem.value = null
  showModal.value = true
}

// Open edit modal
const openEditModal = (item: any) => {
  if (!isAdmin.value) return

  modalMode.value = 'edit'
  modalType.value = activeTab.value
  formData.value = {
    name: item.name,
    description: item.description || ''
  }
  editingItem.value = item
  showModal.value = true
}

// Close modal
const closeModal = () => {
  showModal.value = false
  formData.value = { name: '', description: '' }
  editingItem.value = null
}

// Save (create or update)
const saveItem = async () => {
  if (!formData.value.name.trim()) {
    return
  }

  try {
    const token = localStorage.getItem('token')
    const config = {
      headers: { Authorization: `Bearer ${token}` }
    }

    if (modalMode.value === 'create') {
      await axios.post(getEndpoint(modalType.value), formData.value, config)
    } else {
      await axios.put(`${getEndpoint(modalType.value)}/${editingItem.value.id}`, formData.value, config)
    }

    await loadAllData()
    closeModal()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to save item'
    console.error('Error saving item:', err)
  }
}

// Delete item
const deleteItem = async (item: any) => {
  if (!isAdmin.value) return

  if (!confirm(`Are you sure you want to delete "${item.name}"?`)) {
    return
  }

  try {
    const token = localStorage.getItem('token')
    const config = {
      headers: { Authorization: `Bearer ${token}` }
    }

    await axios.delete(`${getEndpoint(activeTab.value)}/${item.id}`, config)
    await loadAllData()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete item'
    console.error('Error deleting item:', err)
  }
}

onMounted(() => {
  loadAllData()
})
</script>

<template>
  <AppLayout>
    <div class="p-6">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">System Configuration</h1>
        <button
          v-if="isAdmin"
          @click="openCreateModal"
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
        >
          + Add {{ tabs.find(t => t.id === activeTab)?.label }}
        </button>
      </div>

      <!-- Error State -->
      <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <p class="text-red-700 mb-2">{{ error }}</p>
        <button
          @click="loadAllData"
          class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Tabs -->
      <div class="mb-6 border-b border-gray-200">
        <div class="flex overflow-x-auto">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'px-6 py-3 font-medium whitespace-nowrap transition-colors',
              activeTab === tab.id
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            ]"
          >
            {{ tab.icon }} {{ tab.label }}
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading...
      </div>

      <!-- Data Table -->
      <div v-else class="bg-white rounded-lg shadow">
        <!-- Table header -->
        <div class="grid grid-cols-12 gap-4 p-4 border-b font-semibold text-gray-600 text-sm">
          <div class="col-span-3">NAME</div>
          <div class="col-span-7">DESCRIPTION</div>
          <div class="col-span-2 text-right">ACTIONS</div>
        </div>

        <!-- Empty state -->
        <div v-if="currentData.length === 0" class="p-8 text-center text-gray-500">
          No {{ tabs.find(t => t.id === activeTab)?.label.toLowerCase() }} configured yet.
        </div>

        <!-- Data rows -->
        <div
          v-for="item in currentData"
          :key="item.id"
          class="grid grid-cols-12 gap-4 p-4 border-b hover:bg-gray-50 transition-colors"
        >
          <!-- Name -->
          <div class="col-span-3 font-medium">
            {{ item.name }}
          </div>

          <!-- Description -->
          <div class="col-span-7 text-gray-600">
            {{ item.description || 'No description' }}
          </div>

          <!-- Actions -->
          <div class="col-span-2 text-right space-x-2">
            <button
              v-if="isAdmin"
              @click="openEditModal(item)"
              class="text-blue-600 hover:text-blue-800 transition-colors"
              title="Edit"
            >
              ✏️
            </button>
            <button
              v-if="isAdmin"
              @click="deleteItem(item)"
              class="text-red-600 hover:text-red-800 transition-colors"
              title="Delete"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>

      <!-- Create/Edit Modal -->
      <div
        v-if="showModal"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="closeModal"
      >
        <div class="bg-white rounded-lg p-6 w-96 shadow-xl">
          <h2 class="text-xl font-bold mb-4">
            {{ modalMode === 'create' ? 'Add' : 'Edit' }} {{ tabs.find(t => t.id === modalType)?.label }}
          </h2>

          <div class="mb-4">
            <label class="block text-sm font-medium mb-1 text-gray-700">Name *</label>
            <input
              v-model="formData.name"
              type="text"
              class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter name"
              @keyup.enter="saveItem"
            />
          </div>

          <div class="mb-6">
            <label class="block text-sm font-medium mb-1 text-gray-700">Description</label>
            <textarea
              v-model="formData.description"
              class="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              placeholder="Optional description"
            ></textarea>
          </div>

          <div class="flex justify-end space-x-2">
            <button
              @click="closeModal"
              class="px-4 py-2 border rounded hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              @click="saveItem"
              class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              :disabled="!formData.name.trim()"
              :class="{ 'opacity-50 cursor-not-allowed': !formData.name.trim() }"
            >
              {{ modalMode === 'create' ? 'Create' : 'Update' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
