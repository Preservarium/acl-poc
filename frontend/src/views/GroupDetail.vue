<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import AddMemberModal from '@/components/groups/AddMemberModal.vue'
import { fetchGroup, fetchGroupMembers } from '@/api/groups'
import { fetchResourcePermissions, revokePermission } from '@/api/permissions'
import type { Group, User, Permission } from '@/types'

const route = useRoute()
const router = useRouter()

const groupId = computed(() => route.params.id as string)
const group = ref<Group | null>(null)
const members = ref<User[]>([])
const permissions = ref<Permission[]>([])

const loading = ref(false)
const error = ref<string | null>(null)

// Add member modal state
const showAddMemberModal = ref(false)

const loadGroupDetails = async () => {
  loading.value = true
  error.value = null

  try {
    const [groupData, membersData, permissionsData] = await Promise.all([
      fetchGroup(groupId.value),
      fetchGroupMembers(groupId.value),
      fetchResourcePermissions('group', groupId.value)
    ])

    group.value = groupData
    members.value = membersData
    permissions.value = permissionsData
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load group details'
  } finally {
    loading.value = false
  }
}

const openAddMemberModal = () => {
  showAddMemberModal.value = true
}

const handleMemberAdded = async () => {
  showAddMemberModal.value = false
  await loadGroupDetails()
}

const handleRemoveMember = async (userId: string) => {
  if (!confirm('Are you sure you want to remove this member?')) {
    return
  }

  try {
    // Find the permission ID for this user's membership
    const memberPermission = permissions.value.find(
      p => p.grantee_type === 'user' && p.grantee_id === userId && p.resource_type === 'group'
    )

    if (memberPermission) {
      await revokePermission(memberPermission.id)
      await loadGroupDetails()
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to remove member'
  }
}

const getResourceIcon = (type: string) => {
  switch (type) {
    case 'site': return '🏭'
    case 'plan': return '📋'
    case 'sensor': return '📡'
    case 'alarm': return '🔔'
    case 'alert': return '⚠️'
    case 'broker': return '🔌'
    case 'group': return '👥'
    default: return '📄'
  }
}

const getPermissionColor = (permission: string) => {
  switch (permission) {
    case 'manage': return 'bg-purple-100 text-purple-800'
    case 'read': return 'bg-blue-100 text-blue-800'
    case 'write': return 'bg-green-100 text-green-800'
    case 'create': return 'bg-orange-100 text-orange-800'
    case 'delete': return 'bg-red-100 text-red-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

// Get permissions granted to this group (not member permissions)
const groupPermissions = computed(() => {
  return permissions.value.filter(p => p.grantee_type === 'group' && p.grantee_id === groupId.value)
})

onMounted(() => {
  loadGroupDetails()
})
</script>

<template>
  <AppLayout>
    <div class="container mx-auto px-4 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading group details...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="loadGroupDetails"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Group Details -->
      <div v-else-if="group" class="space-y-6">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <button
                @click="router.back()"
                class="text-gray-400 hover:text-gray-600 transition-colors"
              >
                ← Back
              </button>
              <span class="text-3xl">👥</span>
              <h1 class="text-3xl font-bold text-gray-800">{{ group.name }}</h1>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-500">Created:</span>
              <span class="ml-2 text-gray-800">{{ formatDate(group.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- Members Section -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-bold text-gray-800">Members</h2>
            <button
              @click="openAddMemberModal"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              + Add Member
            </button>
          </div>

          <!-- Empty State -->
          <div v-if="members.length === 0" class="text-center py-8 text-gray-500 border border-gray-200 rounded-lg">
            No members in this group yet
          </div>

          <!-- Members List -->
          <div v-else class="space-y-2">
            <div
              v-for="member in members"
              :key="member.id"
              class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div class="flex items-center gap-3">
                <span class="text-2xl">👤</span>
                <div>
                  <div class="font-medium text-gray-800">{{ member.username }}</div>
                  <div class="text-xs text-gray-500">
                    {{ member.is_admin ? 'Administrator' : 'User' }}
                  </div>
                </div>
              </div>
              <button
                @click="handleRemoveMember(member.id)"
                class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        </div>

        <!-- Permissions Section -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Group Permissions</h2>
          <p class="text-gray-600 mb-4">Resources this group has access to:</p>

          <!-- Empty State -->
          <div v-if="groupPermissions.length === 0" class="text-center py-8 text-gray-500 border border-gray-200 rounded-lg">
            This group has no permissions assigned
          </div>

          <!-- Permissions Table -->
          <div v-else class="border rounded-lg overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Resource
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Permission
                  </th>
                  <th class="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Inherit
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Granted By
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="perm in groupPermissions" :key="perm.id" class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center gap-2">
                      <span class="text-xl">{{ getResourceIcon(perm.resource_type) }}</span>
                      <div>
                        <div class="text-sm font-medium text-gray-900">
                          {{ perm.resource_name || perm.resource_id }}
                        </div>
                        <div class="text-xs text-gray-500">{{ perm.resource_type }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full" :class="getPermissionColor(perm.permission)">
                      {{ perm.permission }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span v-if="perm.inherit" class="text-green-600 text-lg">✓</span>
                    <span v-else class="text-gray-300 text-lg">−</span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ perm.granted_by }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Add Member Modal -->
      <AddMemberModal
        v-if="showAddMemberModal && group"
        :group="group"
        :current-members="members"
        @close="showAddMemberModal = false"
        @member-added="handleMemberAdded"
      />
    </div>
  </AppLayout>
</template>

<style scoped>
/* GroupDetail styles */
</style>
