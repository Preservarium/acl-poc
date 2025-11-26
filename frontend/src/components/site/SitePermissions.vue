<template>
  <div class="site-permissions">
    <div class="permissions-header">
      <h2>WHO HAS ACCESS TO THIS SITE</h2>
      <button class="btn-primary" @click="showAddModal = true">
        + Add Permission
      </button>
    </div>

    <div v-if="loading" class="loading">Loading permissions...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="permissions-table">
      <div class="table-header">
        <span class="col-grantee">GRANTEE</span>
        <span class="col-permission">PERMISSION</span>
        <span class="col-inherit">INHERIT</span>
        <span class="col-fields">FIELDS</span>
        <span class="col-actions">ACTIONS</span>
      </div>

      <div v-if="permissions.length === 0" class="no-permissions">
        No permissions set on this site. Click "Add Permission" to grant access.
      </div>

      <div
        v-for="perm in permissions"
        :key="perm.id"
        class="permission-row"
      >
        <div class="row-main">
          <div class="col-grantee">
            <span class="grantee-icon">
              {{ perm.grantee_type === 'group' ? '👥' : '👤' }}
            </span>
            <span class="grantee-name">{{ perm.grantee_name }}</span>
            <span v-if="perm.grantee_type === 'user'" class="direct-badge">
              (direct)
            </span>
          </div>
          <div class="col-permission">
            <span class="permission-badge" :class="`permission-${perm.permission}`">
              {{ perm.permission }}
            </span>
          </div>
          <div class="col-inherit">
            <span class="inherit-indicator" :class="{ inherited: perm.inherit }">
              {{ perm.inherit ? '✓' : '✗' }}
            </span>
          </div>
          <div class="col-fields">
            <span class="fields-list">
              {{ formatFields(perm.fields) }}
            </span>
          </div>
          <div class="col-actions">
            <button class="btn-icon" @click="editPermission(perm)" title="Edit permission">
              ✎
            </button>
            <button class="btn-icon btn-danger" @click="revokePermission(perm)" title="Revoke permission">
              🗑
            </button>
          </div>
        </div>

        <div v-if="perm.grantee_type === 'group' && perm.members" class="row-details">
          └─ Members: {{ formatMembers(perm.members, perm.member_count) }}
        </div>
        <div v-if="perm.expires_at" class="row-details expiration">
          └─ Expires: {{ formatDate(perm.expires_at) }}
        </div>
      </div>
    </div>

    <AddPermissionModal
      v-if="showAddModal"
      resource-type="site"
      :resource-id="siteId"
      @close="showAddModal = false"
      @saved="handlePermissionSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchSitePermissions, revokePermission as revokePermissionApi } from '@/api/permissions'
import type { PermissionWithGrantee } from '@/types'
import AddPermissionModal from '@/components/AddPermissionModal.vue'

interface Props {
  siteId: string
}

const props = defineProps<Props>()

const permissions = ref<PermissionWithGrantee[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showAddModal = ref(false)

const loadPermissions = async () => {
  loading.value = true
  error.value = null
  try {
    permissions.value = await fetchSitePermissions(props.siteId)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load permissions'
    console.error('Failed to load site permissions:', err)
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

const formatMembers = (members?: string[], count?: number): string => {
  if (!members || members.length === 0) {
    return 'No members'
  }

  const displayLimit = 3
  if (members.length <= displayLimit) {
    return members.join(', ')
  }

  const displayed = members.slice(0, displayLimit).join(', ')
  const remaining = (count || members.length) - displayLimit
  return `${displayed} (+${remaining})`
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr)
  return date.toLocaleDateString()
}

const editPermission = (perm: PermissionWithGrantee) => {
  // TODO: Implement edit functionality in Phase 3
  console.log('Edit permission:', perm)
  alert('Edit functionality will be implemented in Phase 3')
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

const handlePermissionSaved = () => {
  showAddModal.value = false
  loadPermissions()
}

onMounted(() => {
  loadPermissions()
})
</script>

<style scoped>
.site-permissions {
  padding: 1rem;
}

.permissions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.permissions-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
}

.btn-primary {
  padding: 0.5rem 1rem;
  background-color: #4f46e5;
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: #4338ca;
}

.loading,
.error {
  padding: 2rem;
  text-align: center;
  color: #666;
}

.error {
  color: #dc2626;
}

.permissions-table {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 3fr 1.5fr 1fr 1.5fr 1fr;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background-color: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  font-weight: 600;
  font-size: 0.75rem;
  color: #6b7280;
  text-transform: uppercase;
}

.no-permissions {
  padding: 2rem;
  text-align: center;
  color: #9ca3af;
}

.permission-row {
  border-bottom: 1px solid #e5e7eb;
}

.permission-row:last-child {
  border-bottom: none;
}

.row-main {
  display: grid;
  grid-template-columns: 3fr 1.5fr 1fr 1.5fr 1fr;
  gap: 1rem;
  padding: 1rem;
  align-items: center;
}

.permission-row:hover .row-main {
  background-color: #f9fafb;
}

.col-grantee {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.grantee-icon {
  font-size: 1.25rem;
}

.grantee-name {
  font-weight: 500;
  color: #111827;
}

.direct-badge {
  color: #6b7280;
  font-size: 0.875rem;
}

.permission-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: lowercase;
}

.permission-manage {
  background-color: #ddd6fe;
  color: #5b21b6;
}

.permission-write {
  background-color: #bfdbfe;
  color: #1e40af;
}

.permission-read {
  background-color: #bbf7d0;
  color: #15803d;
}

.permission-delete {
  background-color: #fecaca;
  color: #991b1b;
}

.permission-create {
  background-color: #fef3c7;
  color: #92400e;
}

.inherit-indicator {
  font-size: 1.125rem;
  color: #9ca3af;
}

.inherit-indicator.inherited {
  color: #10b981;
}

.fields-list {
  color: #6b7280;
  font-size: 0.875rem;
}

.col-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  padding: 0.375rem 0.5rem;
  background-color: transparent;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
}

.btn-icon:hover {
  background-color: #f3f4f6;
  border-color: #9ca3af;
}

.btn-icon.btn-danger:hover {
  background-color: #fef2f2;
  border-color: #fca5a5;
  color: #dc2626;
}

.row-details {
  padding: 0.5rem 1rem 0.75rem 1rem;
  color: #6b7280;
  font-size: 0.875rem;
  background-color: #fafafa;
}

.row-details.expiration {
  color: #f59e0b;
}
</style>
