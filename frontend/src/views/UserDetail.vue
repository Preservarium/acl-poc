<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import EffectivePermissions from '@/components/EffectivePermissions.vue'
import { fetchUser } from '@/api/users'
import type { User } from '@/types'

const route = useRoute()
const user = ref<User | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const userId = computed(() => route.params.id as string)

const loadUser = async () => {
  loading.value = true
  error.value = null
  try {
    user.value = await fetchUser(userId.value)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load user'
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

onMounted(() => {
  loadUser()
})
</script>

<template>
  <AppLayout>
    <div class="container mx-auto px-4 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading user details...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <p class="text-red-600 mb-4">{{ error }}</p>
        <button
          @click="loadUser"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>

      <!-- User Details -->
      <div v-else-if="user" class="space-y-6">
        <!-- User Profile Card -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex justify-between items-start mb-6">
            <div class="flex items-center gap-4">
              <span class="text-5xl">{{ user.is_admin ? '👑' : '👤' }}</span>
              <div>
                <h1 class="text-3xl font-bold text-gray-800">{{ user.username }}</h1>
                <p class="text-gray-600">{{ user.email }}</p>
              </div>
            </div>
            <div class="flex gap-2">
              <button
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Edit
              </button>
              <button
                class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                v-if="!user.is_admin"
              >
                Delete
              </button>
            </div>
          </div>

          <!-- User Info -->
          <div class="grid grid-cols-2 gap-4 border-t pt-4">
            <div>
              <p class="text-sm text-gray-600">Username</p>
              <p class="font-medium">{{ user.username }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-600">Email</p>
              <p class="font-medium">{{ user.email || 'Not set' }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-600">System Admin</p>
              <p class="font-medium">{{ user.is_admin ? 'Yes' : 'No' }}</p>
            </div>
            <div>
              <p class="text-sm text-gray-600">Account Status</p>
              <p class="font-medium">
                <span v-if="!user.is_active" class="text-red-600">Disabled</span>
                <span v-else class="text-green-600">Active</span>
              </p>
            </div>
            <div>
              <p class="text-sm text-gray-600">Created</p>
              <p class="font-medium">{{ user.created_at ? formatDate(user.created_at) : 'Unknown' }}</p>
            </div>
          </div>
        </div>

        <!-- Effective Permissions Section -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <EffectivePermissions :user-id="userId" />
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
/* Add any component-specific styles here */
</style>
