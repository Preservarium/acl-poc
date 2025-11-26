<template>
  <AppLayout>
    <div class="p-6">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">Users</h1>
        <button
          @click="showCreateModal = true"
          class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + Create User
        </button>
      </div>

      <!-- Search -->
      <div class="mb-4">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search users..."
          class="w-full md:w-96 px-4 py-2 border rounded"
        />
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-8 text-gray-500">
        Loading users...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-8 text-red-500">
        {{ error }}
        <button @click="loadUsers" class="ml-2 text-blue-600 hover:underline">Retry</button>
      </div>

      <!-- Users List -->
      <div v-else class="bg-white rounded-lg shadow">
        <div class="grid grid-cols-12 gap-4 p-4 border-b font-semibold text-gray-600">
          <div class="col-span-4">USERNAME</div>
          <div class="col-span-3">ROLE</div>
          <div class="col-span-3">CREATED</div>
          <div class="col-span-2">ACTIONS</div>
        </div>

        <div v-if="filteredUsers.length === 0" class="p-8 text-center text-gray-500">
          No users found.
        </div>

        <div
          v-for="user in filteredUsers"
          :key="user.id"
          class="grid grid-cols-12 gap-4 p-4 border-b hover:bg-gray-50 items-center"
        >
          <div class="col-span-4 flex items-center">
            <span class="text-xl mr-2">{{ user.is_admin ? '👑' : '👤' }}</span>
            <router-link
              :to="`/users/${user.id}`"
              class="font-medium text-blue-600 hover:underline"
            >
              {{ user.username }}
            </router-link>
          </div>
          <div class="col-span-3">
            <span
              :class="user.is_admin ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-800'"
              class="px-2 py-1 rounded text-sm"
            >
              {{ user.is_admin ? 'Admin' : 'User' }}
            </span>
          </div>
          <div class="col-span-3 text-gray-500">
            {{ formatDate(user.created_at) }}
          </div>
          <div class="col-span-2 flex gap-2">
            <router-link
              :to="`/users/${user.id}`"
              class="text-blue-600 hover:text-blue-800"
            >
              View
            </router-link>
            <button
              @click="deleteUser(user)"
              class="text-red-600 hover:text-red-800"
              :disabled="user.is_admin"
              :class="{ 'opacity-50 cursor-not-allowed': user.is_admin }"
            >
              Delete
            </button>
          </div>
        </div>
      </div>

      <!-- Create User Modal -->
      <div v-if="showCreateModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg p-6 w-96">
          <h2 class="text-xl font-bold mb-4">Create User</h2>
          <div class="mb-4">
            <label class="block text-sm font-medium mb-1">Username</label>
            <input v-model="newUser.username" type="text" class="w-full border rounded px-3 py-2" />
          </div>
          <div class="mb-4">
            <label class="block text-sm font-medium mb-1">Password</label>
            <input v-model="newUser.password" type="password" class="w-full border rounded px-3 py-2" />
          </div>
          <div class="mb-4">
            <label class="flex items-center">
              <input v-model="newUser.is_admin" type="checkbox" class="mr-2" />
              <span>Administrator</span>
            </label>
          </div>
          <div class="flex justify-end space-x-2">
            <button @click="showCreateModal = false" class="px-4 py-2 border rounded">Cancel</button>
            <button
              @click="createUser"
              class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              :disabled="!newUser.username || !newUser.password"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import AppLayout from '@/components/AppLayout.vue';
import { fetchUsers, createUser as apiCreateUser, deleteUser as apiDeleteUser } from '@/api/users';

interface User {
  id: string;
  username: string;
  is_admin: boolean;
  created_at: string;
}

const users = ref<User[]>([]);
const loading = ref(true);
const error = ref('');
const searchQuery = ref('');
const showCreateModal = ref(false);
const newUser = ref({
  username: '',
  password: '',
  is_admin: false
});

const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value;
  const query = searchQuery.value.toLowerCase();
  return users.value.filter(u => u.username.toLowerCase().includes(query));
});

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString();
};

const loadUsers = async () => {
  loading.value = true;
  error.value = '';
  try {
    users.value = await fetchUsers();
  } catch (e) {
    error.value = 'Failed to load users';
  } finally {
    loading.value = false;
  }
};

const createUser = async () => {
  try {
    await apiCreateUser(newUser.value);
    showCreateModal.value = false;
    newUser.value = { username: '', password: '', is_admin: false };
    await loadUsers();
  } catch (e) {
    alert('Failed to create user');
  }
};

const deleteUser = async (user: User) => {
  if (user.is_admin) {
    alert('Cannot delete admin users');
    return;
  }
  if (!confirm(`Delete user "${user.username}"?`)) return;
  try {
    await apiDeleteUser(user.id);
    await loadUsers();
  } catch (e) {
    alert('Failed to delete user');
  }
};

onMounted(loadUsers);
</script>
