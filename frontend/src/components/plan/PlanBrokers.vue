<template>
  <div class="plan-brokers">
    <div class="brokers-header">
      <h2 class="section-title">Brokers ({{ brokers.length }})</h2>
      <button
        @click="$emit('create-broker')"
        class="btn-primary"
      >
        + Add Broker
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="brokers.length === 0" class="empty-state">
      <span class="empty-icon">🔌</span>
      <p class="empty-text">No brokers configured for this plan</p>
      <button
        @click="$emit('create-broker')"
        class="btn-secondary"
      >
        Create First Broker
      </button>
    </div>

    <!-- Brokers Table -->
    <div v-else class="brokers-table">
      <table>
        <thead>
          <tr>
            <th class="text-left">Name</th>
            <th class="text-left">Protocol</th>
            <th class="text-left">Status</th>
            <th class="text-left">Host</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="broker in brokers" :key="broker.id" class="broker-row">
            <td>
              <div class="broker-info">
                <span class="broker-icon">🔌</span>
                <span class="broker-name">{{ broker.name }}</span>
              </div>
            </td>
            <td>
              <span class="protocol-badge">{{ broker.protocol }}</span>
            </td>
            <td>
              <span :class="['status-badge', 'status-online']">
                <span class="status-dot"></span>
                Online
              </span>
            </td>
            <td class="host-info">
              {{ getHostInfo(broker.protocol) }}
            </td>
            <td class="text-right">
              <button
                class="btn-action"
              >
                Edit
              </button>
              <button
                class="btn-action btn-danger"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Broker } from '@/types'

const props = defineProps<{
  brokers: Broker[]
}>()

defineEmits<{
  'create-broker': []
}>()

const getHostInfo = (protocol: string): string => {
  if (protocol === 'MQTT') return '192.168.1.100:1883'
  if (protocol === 'CoAP') return '192.168.1.101:5683'
  if (protocol === 'HTTP') return 'http://broker.local:8080'
  if (protocol === 'AMQP') return '192.168.1.102:5672'
  return 'N/A'
}
</script>

<style scoped>
.plan-brokers {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.brokers-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
  background: #2563eb;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #2563eb;
  background: white;
  border: 1px solid #2563eb;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-secondary:hover {
  background: #eff6ff;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem 2rem;
  text-align: center;
  background: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 0.5rem;
}

.empty-icon {
  font-size: 4rem;
  opacity: 0.5;
}

.empty-text {
  font-size: 0.875rem;
  color: #6b7280;
}

.brokers-table {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  overflow: hidden;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f9fafb;
}

th {
  padding: 0.75rem 1.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

tbody tr {
  border-top: 1px solid #e5e7eb;
}

.broker-row {
  transition: background 0.15s ease;
}

.broker-row:hover {
  background: #f9fafb;
}

td {
  padding: 1rem 1.5rem;
}

.broker-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.broker-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.broker-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.protocol-badge {
  display: inline-flex;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #1e40af;
  background: #dbeafe;
  border-radius: 9999px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 9999px;
}

.status-online {
  color: #065f46;
  background: #d1fae5;
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: currentColor;
}

.host-info {
  font-size: 0.875rem;
  color: #6b7280;
  font-family: ui-monospace, SFMono-Regular, monospace;
}

.btn-action {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #2563eb;
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-left: 0.5rem;
}

.btn-action:hover {
  background: #eff6ff;
}

.btn-danger {
  color: #dc2626;
}

.btn-danger:hover {
  background: #fee2e2;
}

@media (max-width: 768px) {
  .brokers-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .brokers-table {
    overflow-x: auto;
  }

  table {
    min-width: 700px;
  }
}
</style>
