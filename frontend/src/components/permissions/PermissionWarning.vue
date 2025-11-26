<script setup lang="ts">
import { computed } from 'vue'

interface ExistingPermission {
  permission: string
  fields?: string[]
  source: string // e.g., "Factory 1 Operators (inherited from site)"
  isInherited?: boolean
  isDirect?: boolean
}

const props = defineProps<{
  existingPermissions: ExistingPermission[]
  selectedPermission: string
  selectedFields?: string[] | null
  granteeName?: string
}>()

// Check if there are any warnings to show
const hasWarnings = computed(() => {
  return props.existingPermissions.length > 0
})

// Get relevant warnings based on the selected permission
const warnings = computed(() => {
  if (!props.existingPermissions.length) return []

  return props.existingPermissions.filter(existing => {
    // Check if the permission already exists (same or higher)
    const permLevels = ['read', 'write', 'delete', 'create', 'manage']
    const existingLevel = permLevels.indexOf(existing.permission)
    const selectedLevel = permLevels.indexOf(props.selectedPermission)

    // Show warning if existing permission is same or higher
    return existingLevel >= selectedLevel
  })
})

// Format fields for display
const formatFields = (fields?: string[]): string => {
  if (!fields || fields.length === 0) return 'all fields'
  return fields.join(', ')
}

// Get warning icon based on severity
const getWarningIcon = (existing: ExistingPermission): string => {
  if (existing.isDirect) return '⚠️'
  if (existing.isInherited) return '📋'
  return 'ℹ️'
}

// Get warning type class
const getWarningClass = (existing: ExistingPermission): string => {
  if (existing.isDirect) return 'warning-direct'
  if (existing.isInherited) return 'warning-inherited'
  return 'warning-group'
}

// Get warning message
const getWarningMessage = (existing: ExistingPermission): string => {
  const grantee = props.granteeName || 'This grantee'
  const fieldsText = formatFields(existing.fields)

  if (existing.isDirect) {
    return `${grantee} already has direct '${existing.permission}' permission on ${fieldsText}`
  }

  return `${grantee} already has '${existing.permission}' permission on ${fieldsText} via ${existing.source}`
}
</script>

<template>
  <div v-if="hasWarnings && warnings.length > 0" class="permission-warnings">
    <div
      v-for="(warning, index) in warnings"
      :key="index"
      class="warning-item"
      :class="getWarningClass(warning)"
    >
      <div class="warning-icon">
        {{ getWarningIcon(warning) }}
      </div>
      <div class="warning-content">
        <div class="warning-message">
          {{ getWarningMessage(warning) }}
        </div>
        <div v-if="warning.source && !warning.isDirect" class="warning-source">
          Source: {{ warning.source }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.permission-warnings {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.warning-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  border-radius: 0.375rem;
  border: 1px solid;
  font-size: 0.875rem;
}

.warning-direct {
  background-color: #fef2f2;
  border-color: #fca5a5;
  color: #991b1b;
}

.warning-inherited {
  background-color: #fefce8;
  border-color: #fde047;
  color: #854d0e;
}

.warning-group {
  background-color: #eff6ff;
  border-color: #93c5fd;
  color: #1e40af;
}

.warning-icon {
  font-size: 1.25rem;
  line-height: 1;
  flex-shrink: 0;
}

.warning-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.warning-message {
  font-weight: 500;
  line-height: 1.4;
}

.warning-source {
  font-size: 0.75rem;
  opacity: 0.8;
  font-style: italic;
}
</style>
