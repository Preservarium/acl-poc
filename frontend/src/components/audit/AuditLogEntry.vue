<template>
  <div class="audit-log-entry">
    <div class="log-timestamp">{{ formattedTimestamp }}</div>
    <div class="log-action">
      <span :class="['action-badge', actionClass]">{{ actionLabel }}</span>
    </div>
    <div class="log-details">
      <div class="log-description">
        {{ logDescription }}
      </div>
      <div v-if="log.details && Object.keys(log.details).length > 0" class="log-metadata">
        <template v-if="log.details.effect">
          <span class="metadata-item">Effect: <strong>{{ log.details.effect }}</strong></span>
        </template>
        <template v-if="log.details.inherit !== undefined">
          <span class="metadata-item">Inherit: <strong>{{ log.details.inherit ? 'Yes' : 'No' }}</strong></span>
        </template>
        <template v-if="log.details.fields">
          <span class="metadata-item">Fields: <strong>{{ log.details.fields.join(', ') }}</strong></span>
        </template>
        <template v-if="log.details.expires_at">
          <span class="metadata-item">Expires: <strong>{{ formatDate(log.details.expires_at) }}</strong></span>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AuditLog } from '@/api/audit'

interface Props {
  log: AuditLog
}

const props = defineProps<Props>()

const formattedTimestamp = computed(() => {
  const date = new Date(props.log.timestamp)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
})

const actionClass = computed(() => {
  switch (props.log.action) {
    case 'permission_granted':
      return 'action-granted'
    case 'permission_revoked':
      return 'action-revoked'
    case 'permission_denied':
      return 'action-denied'
    case 'permission_expired':
      return 'action-expired'
    default:
      return ''
  }
})

const actionLabel = computed(() => {
  switch (props.log.action) {
    case 'permission_granted':
      return 'PERMISSION GRANTED'
    case 'permission_revoked':
      return 'PERMISSION REVOKED'
    case 'permission_denied':
      return 'PERMISSION DENIED'
    case 'permission_expired':
      return 'PERMISSION EXPIRED'
    default:
      return props.log.action.toUpperCase()
  }
})

const logDescription = computed(() => {
  const actor = props.log.actor_name || 'System'
  const permission = props.log.permission || 'permission'

  let target = ''
  if (props.log.target_user_name) {
    target = `user '${props.log.target_user_name}'`
  } else if (props.log.target_group_name) {
    target = `group '${props.log.target_group_name}'`
  }

  let resource = ''
  if (props.log.resource_type && props.log.resource_name) {
    resource = `on ${props.log.resource_type}:${props.log.resource_name}`
  } else if (props.log.resource_type && props.log.resource_id) {
    resource = `on ${props.log.resource_type}:${props.log.resource_id.substring(0, 8)}`
  }

  switch (props.log.action) {
    case 'permission_granted':
      return `${actor} granted '${permission}' to ${target} ${resource}`
    case 'permission_revoked':
      return `${actor} revoked '${permission}' from ${target} ${resource}`
    case 'permission_denied':
      return `${actor} was denied '${permission}' ${resource}`
    case 'permission_expired':
      return `'${permission}' permission for ${target} expired ${resource}`
    default:
      return `${actor} performed ${props.log.action} on ${target} ${resource}`
  }
})

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
}
</script>

<style scoped>
.audit-log-entry {
  display: grid;
  grid-template-columns: 180px 200px 1fr;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  align-items: start;
}

.audit-log-entry:hover {
  background-color: #f9fafb;
}

.log-timestamp {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.875rem;
  color: #6b7280;
  white-space: nowrap;
}

.log-action {
  display: flex;
  align-items: center;
}

.action-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.action-granted {
  background-color: #d1fae5;
  color: #065f46;
}

.action-revoked {
  background-color: #fee2e2;
  color: #991b1b;
}

.action-denied {
  background-color: #fef3c7;
  color: #92400e;
}

.action-expired {
  background-color: #e0e7ff;
  color: #3730a3;
}

.log-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.log-description {
  font-size: 0.875rem;
  color: #111827;
  line-height: 1.5;
}

.log-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.metadata-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.metadata-item strong {
  color: #374151;
}

@media (max-width: 768px) {
  .audit-log-entry {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }

  .log-timestamp {
    font-size: 0.75rem;
  }

  .action-badge {
    font-size: 0.625rem;
    padding: 0.125rem 0.5rem;
  }
}
</style>
