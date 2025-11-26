<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { fetchUsers } from '@/api/users'
import { fetchGroupPermissions, addGroupMember } from '@/api/groups'
import MembershipPreview from './MembershipPreview.vue'
import type { Group, User, Permission } from '@/types'

interface Props {
  group: Group
  currentMembers: User[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  memberAdded: []
}>()

const allUsers = ref<User[]>([])
const groupPermissions = ref<Permission[]>([])
const selectedUserIds = ref<Set<string>>(new Set())
const searchQuery = ref('')
const setExpiration = ref(false)
const expirationDate = ref('')

const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

// Filter users based on search
const filteredUsers = computed(() => {
  const query = searchQuery.value.toLowerCase()
  return allUsers.value.filter(user => {
    const matchesSearch = !query ||
      user.username.toLowerCase().includes(query) ||
      (user.email && user.email.toLowerCase().includes(query))
    return matchesSearch
  })
})

// Separate members from non-members
const nonMembers = computed(() => {
  const memberIds = new Set(props.currentMembers.map(m => m.id.toString()))
  return filteredUsers.value.filter(u => !memberIds.has(u.id.toString()))
})

const existingMembers = computed(() => {
  const memberIds = new Set(props.currentMembers.map(m => m.id.toString()))
  return filteredUsers.value.filter(u => memberIds.has(u.id.toString()))
})

const isUserSelected = (userId: string) => {
  return selectedUserIds.value.has(userId)
}

const toggleUserSelection = (userId: string) => {
  if (selectedUserIds.value.has(userId)) {
    selectedUserIds.value.delete(userId)
  } else {
    selectedUserIds.value.add(userId)
  }
  // Force reactivity
  selectedUserIds.value = new Set(selectedUserIds.value)
}

const selectedCount = computed(() => selectedUserIds.value.size)

const canSubmit = computed(() => {
  return selectedCount.value > 0 && !saving.value
})

const loadData = async () => {
  loading.value = true
  error.value = null

  try {
    // Load users and group permissions in parallel
    const [usersData, permissionsData] = await Promise.all([
      fetchUsers(),
      fetchGroupPermissions(props.group.id)
    ])

    allUsers.value = usersData
    groupPermissions.value = permissionsData
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load data'
    console.error('Failed to load data:', err)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!canSubmit.value) return

  saving.value = true
  error.value = null

  try {
    // Add each selected user to the group
    const promises = Array.from(selectedUserIds.value).map(userId =>
      addGroupMember(props.group.id, userId)
    )

    await Promise.all(promises)
    emit('memberAdded')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to add members'
    console.error('Failed to add members:', err)
  } finally {
    saving.value = false
  }
}

const handleClose = () => {
  if (!saving.value) {
    emit('close')
  }
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <Transition name="modal">
    <div
      class="modal-overlay"
      @click.self="handleClose"
    >
      <div class="modal-content">
        <!-- Header -->
        <div class="modal-header">
          <div class="header-title">
            <span class="text-2xl">👤</span>
            <h2>Add Member to Group</h2>
          </div>
          <button
            @click="handleClose"
            class="btn-close"
            :disabled="saving"
          >
            ✕
          </button>
        </div>

        <!-- Body -->
        <div class="modal-body">
          <!-- Loading State -->
          <div v-if="loading" class="text-center py-8 text-gray-500">
            Loading...
          </div>

          <!-- Error Message -->
          <div v-else-if="error" class="error-message">
            {{ error }}
          </div>

          <!-- Main Content -->
          <div v-else>
            <!-- Group Info -->
            <div class="group-info">
              <label class="label">Group:</label>
              <div class="group-name">
                <span class="text-xl">👥</span>
                <span>{{ group.name }}</span>
              </div>
            </div>

            <!-- Permissions Preview -->
            <div class="preview-section">
              <label class="label">This will grant the user:</label>
              <MembershipPreview :permissions="groupPermissions" />
            </div>

            <!-- User Selection -->
            <div class="select-section">
              <label class="label">Select User:</label>

              <!-- Search Input -->
              <div class="search-box">
                <span class="search-icon">🔍</span>
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="Search users..."
                  class="search-input"
                />
              </div>

              <!-- Users List -->
              <div class="users-list">
                <!-- Non-members (selectable) -->
                <div v-if="nonMembers.length > 0" class="user-section">
                  <div
                    v-for="user in nonMembers"
                    :key="user.id"
                    class="user-item selectable"
                    @click="toggleUserSelection(user.id.toString())"
                  >
                    <input
                      type="checkbox"
                      :checked="isUserSelected(user.id.toString())"
                      @click.stop="toggleUserSelection(user.id.toString())"
                      class="checkbox"
                    />
                    <span class="user-icon">👤</span>
                    <div class="user-info">
                      <div class="user-name">{{ user.username }}</div>
                      <div v-if="user.email" class="user-email">{{ user.email }}</div>
                    </div>
                  </div>
                </div>

                <!-- Already Members -->
                <div v-if="existingMembers.length > 0" class="user-section">
                  <div class="section-header">Already members:</div>
                  <div
                    v-for="user in existingMembers"
                    :key="user.id"
                    class="user-item disabled"
                  >
                    <input
                      type="checkbox"
                      checked
                      disabled
                      class="checkbox"
                    />
                    <span class="user-icon">👤</span>
                    <div class="user-info">
                      <div class="user-name">{{ user.username }}</div>
                      <div v-if="user.email" class="user-email">{{ user.email }}</div>
                    </div>
                  </div>
                </div>

                <!-- Empty State -->
                <div v-if="filteredUsers.length === 0" class="empty-state">
                  <p class="text-gray-500 text-sm">
                    {{ searchQuery ? 'No users match your search' : 'No users available' }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Options -->
            <div class="options-section">
              <label class="label">Options:</label>
              <div class="option-item">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    v-model="setExpiration"
                    class="checkbox"
                  />
                  <span>Set membership expiration</span>
                </label>
                <div v-if="setExpiration" class="expiration-input">
                  <label class="text-sm text-gray-600">Expires:</label>
                  <input
                    v-model="expirationDate"
                    type="date"
                    class="date-input"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="modal-footer">
          <button
            @click="handleClose"
            class="btn-secondary"
            :disabled="saving"
          >
            Cancel
          </button>
          <button
            @click="handleSubmit"
            class="btn-primary"
            :disabled="!canSubmit"
          >
            {{ saving ? 'Adding...' : `Add ${selectedCount > 0 ? selectedCount : ''} Member${selectedCount !== 1 ? 's' : ''}` }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.header-title h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.2s;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover:not(:disabled) {
  color: #374151;
}

.btn-close:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.group-info {
  margin-bottom: 1rem;
}

.label {
  display: block;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.group-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.preview-section {
  margin-bottom: 1.5rem;
}

.select-section {
  margin-bottom: 1.5rem;
}

.search-box {
  position: relative;
  margin-bottom: 0.75rem;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #374151;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.users-list {
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  max-height: 300px;
  overflow-y: auto;
}

.user-section {
  display: flex;
  flex-direction: column;
}

.section-header {
  padding: 0.5rem 0.75rem;
  background-color: #f9fafb;
  border-top: 1px solid #e5e7eb;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.15s;
}

.user-item:last-child {
  border-bottom: none;
}

.user-item.selectable {
  cursor: pointer;
}

.user-item.selectable:hover {
  background-color: #f9fafb;
}

.user-item.disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: #f9fafb;
}

.checkbox {
  cursor: pointer;
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.user-item.disabled .checkbox {
  cursor: not-allowed;
}

.user-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 500;
  color: #1f2937;
  font-size: 0.875rem;
}

.user-email {
  font-size: 0.75rem;
  color: #6b7280;
}

.empty-state {
  padding: 2rem;
  text-align: center;
}

.options-section {
  margin-bottom: 0.5rem;
}

.option-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: #374151;
}

.expiration-input {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: 1.5rem;
}

.date-input {
  padding: 0.375rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  color: #374151;
}

.date-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.error-message {
  padding: 0.75rem;
  background-color: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 0.375rem;
  color: #dc2626;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.btn-primary {
  background-color: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2563eb;
}

.btn-primary:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #f9fafb;
}

.btn-secondary:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
}
</style>
