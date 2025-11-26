<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchPlanPermissions, revokePermission as revokePermissionApi } from '@/api/permissions'
import EffectiveAccessList from '@/components/EffectiveAccessList.vue'
import type { PlanPermissionsResponse, PermissionWithGrantee } from '@/types'

interface Props {
  planId: string
}

const props = defineProps<Props>()

const permissionsData = ref<PlanPermissionsResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const showAddModal = ref(false)

const loadPermissions = async () => {
  loading.value = true
  error.value = null
  try {
    permissionsData.value = await fetchPlanPermissions(props.planId)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load permissions'
    console.error('Failed to load plan permissions:', err)
  } finally {
    loading.value = false
  }
}

const formatFields = (fields?: string[]): string => {
  if (!fields || fields.length === 0) {
    return 'All'
  }
  return fields.join(', ')
}

const formatMembers = (count?: number): string => {
  if (!count || count === 0) {
    return 'No members'
  }
  return count === 1 ? '1 member' : `${count} members`
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString()
}

const editPermission = (perm: PermissionWithGrantee) => {
  // TODO: Implement edit functionality
  console.log('Edit permission:', perm)
  alert('Edit functionality will be implemented in a future phase')
}

const revokePermission = async (perm: PermissionWithGrantee) => {
  if (!confirm(`Are you sure you want to revoke ${perm.permission} permission for ${perm.grantee_name}?`)) {
    return
  }

  try {
    await revokePermissionApi(perm.id)
    await loadPermissions()
  } catch (err: any) {
    alert(err.response?.data?.detail || 'Failed to revoke permission')
    console.error('Failed to revoke permission:', err)
  }
}

const handleAddPermission = () => {
  showAddModal.value = true
  // TODO: Implement add permission modal
  alert('Add permission functionality will be implemented in a future phase')
  showAddModal.value = false
}

onMounted(() => {
  loadPermissions()
})
</script>

<template>
  <div class="plan-permissions">
    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="text-center py-8 text-gray-500">
        Loading permissions...
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6">
        <p class="text-red-700">{{ error }}</p>
      </div>
    </div>

    <!-- Permissions Content -->
    <div v-else-if="permissionsData" class="space-y-6">
      <!-- Inherited Section -->
      <section class="permissions-section inherited">
        <div class="section-header">
          <h3 class="text-lg font-semibold text-gray-700">
            INHERITED FROM PARENT
            <span class="parent-info text-sm font-normal text-gray-500">
              ({{ permissionsData.parent.type }}:{{ permissionsData.parent.name }})
            </span>
          </h3>
        </div>
        <div class="permissions-list bg-gray-50 rounded-lg p-4">
          <div v-if="permissionsData.inherited.length === 0" class="empty-state">
            No inherited permissions
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="perm in permissionsData.inherited"
              :key="perm.id"
              class="permission-row bg-white rounded-lg p-4 border border-gray-200"
            >
              <div class="flex items-start justify-between">
                <div class="flex items-start gap-3 flex-1">
                  <span class="grantee-icon text-xl">
                    {{ perm.grantee_type === 'group' ? '👥' : '👤' }}
                  </span>
                  <div class="flex-1">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="font-medium text-gray-900">{{ perm.grantee_name }}</span>
                      <span
                        class="permission-badge px-2 py-1 rounded-full text-xs font-semibold"
                        :class="{
                          'bg-purple-100 text-purple-800': perm.permission === 'manage',
                          'bg-blue-100 text-blue-800': perm.permission === 'read',
                          'bg-green-100 text-green-800': perm.permission === 'write',
                          'bg-orange-100 text-orange-800': perm.permission === 'create',
                          'bg-red-100 text-red-800': perm.permission === 'delete'
                        }"
                      >
                        {{ perm.permission }}
                      </span>
                      <span class="inherit-badge text-xs text-green-600">
                        ✓ inherit
                      </span>
                      <span class="fields-badge text-xs text-gray-600">
                        {{ formatFields(perm.fields) }}
                      </span>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                      └─ From: {{ perm.source }}
                    </div>
                    <div v-if="perm.member_count" class="text-xs text-gray-500 mt-1">
                      └─ {{ formatMembers(perm.member_count) }}
                    </div>
                  </div>
                </div>
                <div class="text-xs text-gray-400 italic ml-4">
                  (read-only)
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Direct Section -->
      <section class="permissions-section direct">
        <div class="section-header flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-900">
            DIRECT PERMISSIONS
            <span class="text-sm font-normal text-gray-500">(on this plan only)</span>
          </h3>
          <button
            @click="handleAddPermission"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            + Add Permission
          </button>
        </div>
        <div class="permissions-list bg-white rounded-lg p-4 border border-gray-200">
          <div v-if="permissionsData.direct.length === 0" class="empty-state">
            No direct permissions. Add a permission to grant access to specific users or groups on this plan only.
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="perm in permissionsData.direct"
              :key="perm.id"
              class="permission-row bg-gray-50 rounded-lg p-4 border border-gray-200"
            >
              <div class="flex items-start justify-between">
                <div class="flex items-start gap-3 flex-1">
                  <span class="grantee-icon text-xl">
                    {{ perm.grantee_type === 'group' ? '👥' : '👤' }}
                  </span>
                  <div class="flex-1">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="font-medium text-gray-900">{{ perm.grantee_name }}</span>
                      <span
                        class="permission-badge px-2 py-1 rounded-full text-xs font-semibold"
                        :class="{
                          'bg-purple-100 text-purple-800': perm.permission === 'manage',
                          'bg-blue-100 text-blue-800': perm.permission === 'read',
                          'bg-green-100 text-green-800': perm.permission === 'write',
                          'bg-orange-100 text-orange-800': perm.permission === 'create',
                          'bg-red-100 text-red-800': perm.permission === 'delete'
                        }"
                      >
                        {{ perm.permission }}
                      </span>
                      <span
                        class="inherit-badge text-xs"
                        :class="perm.inherit ? 'text-green-600' : 'text-gray-400'"
                      >
                        {{ perm.inherit ? '✓' : '✗' }}
                      </span>
                      <span class="fields-badge text-xs text-gray-600">
                        {{ formatFields(perm.fields) }}
                      </span>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                      └─ Can {{ perm.permission }} {{ perm.fields ? `fields ${perm.fields.join(', ')}` : 'all fields' }} on this plan{{ perm.inherit ? ' and children' : ' only' }}
                    </div>
                    <div v-if="perm.expires_at" class="text-xs text-orange-600 mt-1">
                      └─ Expires: {{ formatDate(perm.expires_at) }}
                    </div>
                    <div v-if="perm.member_count" class="text-xs text-gray-500 mt-1">
                      └─ {{ formatMembers(perm.member_count) }}
                    </div>
                  </div>
                </div>
                <div class="flex gap-2">
                  <button
                    @click="editPermission(perm)"
                    class="text-blue-600 hover:text-blue-800 transition-colors"
                    title="Edit permission"
                  >
                    ✎
                  </button>
                  <button
                    @click="revokePermission(perm)"
                    class="text-red-600 hover:text-red-800 transition-colors"
                    title="Revoke permission"
                  >
                    🗑
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Effective Access Section -->
      <section class="permissions-section effective">
        <div class="section-header">
          <h3 class="text-lg font-semibold text-gray-900">
            EFFECTIVE ACCESS
            <span class="text-sm font-normal text-gray-500">(combined)</span>
          </h3>
        </div>
        <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <EffectiveAccessList :permissions="permissionsData.effective" />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.plan-permissions {
  padding: 0;
}

.permissions-section {
  margin-bottom: 1.5rem;
}

.section-header {
  margin-bottom: 1rem;
}

.parent-info {
  margin-left: 0.5rem;
}

.permissions-list {
  min-height: 4rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
  font-size: 0.875rem;
}

.permission-row {
  transition: all 0.2s ease;
}

.permission-row:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Inherited section has slightly grayed background */
.inherited .permissions-list {
  background-color: #f9fafb;
}

.inherited .permission-row {
  background-color: #ffffff;
}

/* Direct section has white background */
.direct .permissions-list {
  background-color: #ffffff;
}

.direct .permission-row {
  background-color: #f9fafb;
}

/* Effective section has blue tint */
.effective {
  background-color: #eff6ff;
}
</style>
