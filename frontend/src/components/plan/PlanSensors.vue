<template>
  <div class="plan-sensors">
    <div class="sensors-header">
      <h2 class="section-title">Sensors ({{ sensors.length }})</h2>
      <button
        @click="$emit('create-sensor')"
        class="btn-primary"
      >
        + Add Sensor
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="sensors.length === 0" class="empty-state">
      <span class="empty-icon">📡</span>
      <p class="empty-text">No sensors configured for this plan</p>
      <button
        @click="$emit('create-sensor')"
        class="btn-secondary"
      >
        Create First Sensor
      </button>
    </div>

    <!-- Sensors Table -->
    <div v-else class="sensors-table">
      <table>
        <thead>
          <tr>
            <th class="text-left">Name</th>
            <th class="text-left">Type</th>
            <th class="text-left">Status</th>
            <th class="text-left">Last Reading</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="sensor in sensors" :key="sensor.id" class="sensor-row">
            <td>
              <div class="sensor-info">
                <span class="sensor-icon">📡</span>
                <span class="sensor-name">{{ sensor.name }}</span>
              </div>
            </td>
            <td>
              <span class="type-badge">{{ getSensorType(sensor.name) }}</span>
            </td>
            <td>
              <span :class="['status-badge', getStatusClass()]">
                <span class="status-dot"></span>
                {{ getStatus() }}
              </span>
            </td>
            <td class="last-reading">
              {{ getLastReading(sensor.name) }}
            </td>
            <td class="text-right">
              <button
                @click="$emit('view-sensor', sensor.id)"
                class="btn-view"
              >
                View
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Sensor } from '@/types'

const props = defineProps<{
  sensors: Sensor[]
}>()

defineEmits<{
  'create-sensor': []
  'view-sensor': [sensorId: string]
}>()

const getSensorType = (name: string): string => {
  const lower = name.toLowerCase()
  if (lower.includes('temp')) return 'Temperature'
  if (lower.includes('humid')) return 'Humidity'
  if (lower.includes('pressure')) return 'Pressure'
  if (lower.includes('motion')) return 'Motion'
  return 'Generic'
}

const getStatus = (): string => {
  return 'Active'
}

const getStatusClass = (): string => {
  return 'status-active'
}

const getLastReading = (name: string): string => {
  const lower = name.toLowerCase()
  if (lower.includes('temp')) return '23.5°C'
  if (lower.includes('humid')) return '65%'
  if (lower.includes('pressure')) return '1013 hPa'
  if (lower.includes('motion')) return 'No motion'
  return '--'
}
</script>

<style scoped>
.plan-sensors {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sensors-header {
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

.sensors-table {
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

.sensor-row {
  transition: background 0.15s ease;
}

.sensor-row:hover {
  background: #f9fafb;
}

td {
  padding: 1rem 1.5rem;
}

.sensor-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sensor-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.sensor-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.type-badge {
  display: inline-flex;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #1f2937;
  background: #f3f4f6;
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

.status-active {
  color: #065f46;
  background: #d1fae5;
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: currentColor;
}

.last-reading {
  font-size: 0.875rem;
  color: #6b7280;
}

.btn-view {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #2563eb;
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-view:hover {
  background: #eff6ff;
}

@media (max-width: 768px) {
  .sensors-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .sensors-table {
    overflow-x: auto;
  }

  table {
    min-width: 700px;
  }
}
</style>
