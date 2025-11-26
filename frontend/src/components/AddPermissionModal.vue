<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>🔐 Add Permission</h2>
        <button class="btn-close" @click="$emit('close')">&times;</button>
      </div>

      <div class="modal-body">
        <!-- Resource Display with Hierarchy -->
        <div class="form-section">
          <label class="form-label">Resource</label>
          <div class="resource-hierarchy">
            <div class="resource-info primary">
              <span class="resource-icon">
                {{ getResourceIcon(resourceType) }}
              </span>
              <span class="resource-name">{{ resourceType }}:{{ resourceName || resourceId }}</span>
            </div>
            <div v-if="resourceHierarchy.length > 0" class="parent-resources">
              <div
                v-for="parent in resourceHierarchy"
                :key="parent.id"
                class="parent-resource"
              >
                <span class="hierarchy-connector">└─</span>
                <span class="resource-icon">{{ getResourceIcon(parent.type) }}</span>
                <span class="resource-name">{{ parent.type }}:{{ parent.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Grantee Type Toggle -->
        <div class="form-section">
          <label class="form-label">Grantee Type</label>
          <div class="radio-group">
            <label class="radio-option" :class="{ active: granteeType === 'group' }">
              <input
                type="radio"
                value="group"
                v-model="granteeType"
                @change="resetGrantee"
              />
              <span>👥 Group</span>
            </label>
            <label class="radio-option" :class="{ active: granteeType === 'user' }">
              <input
                type="radio"
                value="user"
                v-model="granteeType"
                @change="resetGrantee"
              />
              <span>👤 User</span>
            </label>
          </div>
        </div>

        <!-- Searchable Grantee Selection -->
        <div class="form-section">
          <label class="form-label">
            Select {{ granteeType === 'group' ? 'Group' : 'User' }}
          </label>
          <div class="search-select-wrapper">
            <div class="search-input-container">
              <span class="search-icon">🔍</span>
              <input
                type="text"
                v-model="searchQuery"
                :placeholder="`Search ${granteeType}...`"
                class="search-input"
                @focus="showDropdown = true"
              />
            </div>
            <div v-if="showDropdown && filteredGrantees.length > 0" class="dropdown-list">
              <button
                v-for="option in filteredGrantees"
                :key="option.id"
                type="button"
                class="dropdown-item"
                :class="{ selected: granteeId === option.id }"
                @click="selectGrantee(option)"
              >
                <span class="check-icon">{{ granteeId === option.id ? '✓' : '' }}</span>
                <span class="grantee-icon">{{ granteeType === 'user' ? '👤' : '👥' }}</span>
                <div class="grantee-info">
                  <div class="grantee-name">{{ option.name }}</div>
                  <div v-if="option.email" class="grantee-email">{{ option.email }}</div>
                </div>
              </button>
            </div>
            <div v-if="granteeId && selectedGranteeName" class="selected-grantee">
              <span class="check-icon">✓</span>
              <span class="grantee-icon">{{ granteeType === 'user' ? '👤' : '👥' }}</span>
              <span class="grantee-name">{{ selectedGranteeName }}</span>
              <button type="button" class="clear-btn" @click="clearGrantee">&times;</button>
            </div>
          </div>
        </div>

        <!-- Permission Type Selection -->
        <div class="form-section">
          <label class="form-label">Permission</label>
          <div class="permission-grid">
            <label
              v-for="perm in availablePermissions"
              :key="perm.type"
              class="permission-option"
              :class="{ active: permission === perm.type }"
            >
              <input type="radio" :value="perm.type" v-model="permission" />
              <div class="permission-content">
                <div class="permission-name">{{ perm.type }}</div>
                <div class="permission-description">{{ perm.description }}</div>
              </div>
            </label>
          </div>
        </div>

        <!-- Options Section -->
        <div class="form-section">
          <label class="form-label">Options</label>

          <!-- Inherit to Children -->
          <div class="option-item">
            <label class="checkbox-option">
              <input type="checkbox" v-model="inherit" />
              <span>☑ Inherit to children</span>
            </label>
          </div>

          <!-- Restrict to Specific Fields -->
          <div class="option-item">
            <label class="checkbox-option">
              <input type="checkbox" v-model="enableFieldRestriction" />
              <span>☑ Restrict to specific fields</span>
            </label>
            <div v-if="enableFieldRestriction" class="nested-option">
              <FieldSelector
                :available-fields="availableFields"
                v-model="selectedFields"
              />
            </div>
          </div>

          <!-- Expiration Date -->
          <div class="option-item">
            <ExpirationPicker v-model="expiresAt" />
          </div>
        </div>

        <!-- Permission Warnings -->
        <PermissionWarning
          v-if="granteeId"
          :existing-permissions="existingPermissions"
          :selected-permission="permission"
          :selected-fields="enableFieldRestriction ? selectedFields : null"
          :grantee-name="selectedGranteeName"
        />

        <!-- Error Message -->
        <div v-if="error" class="error-message">{{ error }}</div>
      </div>

      <div class="modal-footer">
        <button class="btn-secondary" @click="$emit('close')">Cancel</button>
        <button
          class="btn-primary"
          @click="handleSubmit"
          :disabled="!isFormValid || saving"
        >
          {{ saving ? 'Granting...' : 'Grant Permission' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { grantPermission, fetchResourceHierarchy, checkExistingPermissions } from '@/api/permissions'
import apiClient from '@/api/client'
import type { ResourceType, GranteeType } from '@/types'
import FieldSelector from './permissions/FieldSelector.vue'
import ExpirationPicker from './permissions/ExpirationPicker.vue'
import PermissionWarning from './permissions/PermissionWarning.vue'

interface Props {
  resourceType: ResourceType
  resourceId: string
  resourceName?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

interface GranteeOption {
  id: string
  name: string
  email?: string
}

const granteeType = ref<GranteeType>('group')
const granteeId = ref('')
const selectedGranteeName = ref('')
const searchQuery = ref('')
const showDropdown = ref(false)
const permission = ref('read')
const inherit = ref(true)
const enableFieldRestriction = ref(false)
const selectedFields = ref<string[] | null>(null)
const expiresAt = ref<string | null>(null)
const saving = ref(false)
const error = ref<string | null>(null)

const granteeOptions = ref<GranteeOption[]>([])
const resourceHierarchy = ref<Array<{ type: string; id: string; name: string }>>([])
const existingPermissions = ref<Array<{
  permission: string
  fields?: string[]
  source: string
  isInherited?: boolean
  isDirect?: boolean
}>>([])

const availablePermissions = [
  { type: 'read', description: 'View resource data' },
  { type: 'write', description: 'Modify resource data' },
  { type: 'delete', description: 'Remove resource' },
  { type: 'create', description: 'Create child resources' },
  { type: 'manage', description: 'Full control including permissions' }
]

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
    default:
      return []
  }
})

const filteredGrantees = computed(() => {
  if (!searchQuery.value) {
    return granteeOptions.value.slice(0, 10)
  }
  const query = searchQuery.value.toLowerCase()
  return granteeOptions.value.filter(
    option =>
      option.name.toLowerCase().includes(query) ||
      option.email?.toLowerCase().includes(query)
  ).slice(0, 10)
})

const isFormValid = computed(() => {
  return granteeId.value && permission.value
})

const getResourceIcon = (type: string): string => {
  const icons: Record<string, string> = {
    site: '🏭',
    plan: '📋',
    sensor: '📡',
    broker: '🔌',
    alarm: '🔔',
    alert: '⚠️',
    dashboard: '📊',
    group: '👥',
    user: '👤'
  }
  return icons[type] || '📦'
}

const resetGrantee = () => {
  granteeId.value = ''
  selectedGranteeName.value = ''
  searchQuery.value = ''
  showDropdown.value = false
  existingPermissions.value = []
  loadGranteeOptions()
}

const selectGrantee = (option: GranteeOption) => {
  granteeId.value = option.id
  selectedGranteeName.value = option.name
  searchQuery.value = ''
  showDropdown.value = false

  // Load existing permissions for this grantee
  loadExistingPermissions()
}

const clearGrantee = () => {
  granteeId.value = ''
  selectedGranteeName.value = ''
  searchQuery.value = ''
  existingPermissions.value = []
}

const loadGranteeOptions = async () => {
  try {
    if (granteeType.value === 'group') {
      const response = await apiClient.get<Array<{ id: string; name: string }>>('/groups')
      granteeOptions.value = response.data
    } else {
      const response = await apiClient.get<Array<{ id: string; username: string; email?: string }>>('/users')
      granteeOptions.value = response.data.map((user) => ({
        id: user.id,
        name: user.username,
        email: user.email
      }))
    }
  } catch (err: any) {
    console.error('Failed to load grantee options:', err)
    error.value = 'Failed to load available grantees'
  }
}

const loadResourceHierarchy = async () => {
  try {
    const hierarchy = await fetchResourceHierarchy(props.resourceType, props.resourceId)
    resourceHierarchy.value = hierarchy
  } catch (err) {
    console.warn('Could not load resource hierarchy:', err)
    resourceHierarchy.value = []
  }
}

const loadExistingPermissions = async () => {
  if (!granteeId.value) return

  try {
    const existing = await checkExistingPermissions(
      granteeType.value,
      granteeId.value,
      props.resourceType,
      props.resourceId
    )
    existingPermissions.value = existing
  } catch (err) {
    console.warn('Could not load existing permissions:', err)
    existingPermissions.value = []
  }
}

const handleSubmit = async () => {
  if (!isFormValid.value) {
    return
  }

  saving.value = true
  error.value = null

  try {
    const grantData: any = {
      grantee_type: granteeType.value,
      grantee_id: granteeId.value,
      resource_type: props.resourceType,
      resource_id: props.resourceId,
      permission: permission.value as any,
      effect: 'allow',
      inherit: inherit.value
    }

    // Add optional fields
    if (expiresAt.value) {
      grantData.expires_at = expiresAt.value
    }

    if (enableFieldRestriction.value && selectedFields.value && selectedFields.value.length > 0) {
      grantData.fields = selectedFields.value
    }

    await grantPermission(grantData)

    emit('saved')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to grant permission'
    console.error('Failed to grant permission:', err)
  } finally {
    saving.value = false
  }
}

// Click outside to close dropdown
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.search-select-wrapper')) {
    showDropdown.value = false
  }
}

onMounted(() => {
  loadGranteeOptions()
  loadResourceHierarchy()
  document.addEventListener('click', handleClickOutside)
})

// Cleanup
import { onUnmounted } from 'vue'
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

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
  max-width: 650px;
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

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color 0.2s;
}

.btn-close:hover {
  color: #374151;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.form-section {
  margin-bottom: 1.5rem;
}

.form-section:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

/* Resource Hierarchy */
.resource-hierarchy {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.resource-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
}

.resource-info.primary {
  background-color: #eff6ff;
  border-color: #bfdbfe;
}

.resource-icon {
  font-size: 1.25rem;
}

.resource-name {
  color: #374151;
  font-size: 0.875rem;
  font-family: monospace;
  font-weight: 500;
}

.parent-resources {
  padding-left: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.parent-resource {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.hierarchy-connector {
  color: #9ca3af;
  font-family: monospace;
}

/* Radio Group */
.radio-group {
  display: flex;
  gap: 0.75rem;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 2px solid #d1d5db;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
  justify-content: center;
  font-weight: 500;
}

.radio-option:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

.radio-option.active {
  background-color: #eff6ff;
  border-color: #4f46e5;
  color: #4f46e5;
}

.radio-option input[type='radio'] {
  cursor: pointer;
}

/* Search Select */
.search-select-wrapper {
  position: relative;
}

.search-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  font-size: 1rem;
}

.search-input {
  width: 100%;
  padding: 0.5rem 0.75rem 0.5rem 2.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #374151;
  background-color: white;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.dropdown-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 0.25rem;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s;
}

.dropdown-item:hover {
  background-color: #f9fafb;
}

.dropdown-item.selected {
  background-color: #eff6ff;
}

.check-icon {
  width: 1.25rem;
  font-weight: bold;
  color: #10b981;
}

.grantee-icon {
  font-size: 1.25rem;
}

.grantee-info {
  flex: 1;
}

.grantee-name {
  font-weight: 500;
  color: #374151;
}

.grantee-email {
  font-size: 0.75rem;
  color: #6b7280;
}

.selected-grantee {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  margin-top: 0.5rem;
  background-color: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 0.375rem;
}

.clear-btn {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #9ca3af;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.clear-btn:hover {
  color: #374151;
}

/* Permission Grid */
.permission-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.permission-option {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 2px solid #d1d5db;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.permission-option:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

.permission-option.active {
  background-color: #eff6ff;
  border-color: #4f46e5;
}

.permission-option input[type='radio'] {
  margin-top: 0.125rem;
  cursor: pointer;
}

.permission-content {
  flex: 1;
}

.permission-name {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
  text-transform: capitalize;
}

.permission-description {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
  line-height: 1.3;
}

/* Options */
.option-item {
  margin-bottom: 0.75rem;
}

.option-item:last-child {
  margin-bottom: 0;
}

.checkbox-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  color: #374151;
}

.checkbox-option input[type='checkbox'] {
  cursor: pointer;
  width: 1rem;
  height: 1rem;
  accent-color: #4f46e5;
}

.nested-option {
  margin-top: 0.75rem;
  margin-left: 1.5rem;
  padding: 0.75rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
}

/* Error Message */
.error-message {
  padding: 0.75rem;
  background-color: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 0.375rem;
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 1rem;
}

/* Modal Footer */
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
}

.btn-primary {
  background-color: #4f46e5;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #4338ca;
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

.btn-secondary:hover {
  background-color: #f9fafb;
}
</style>
