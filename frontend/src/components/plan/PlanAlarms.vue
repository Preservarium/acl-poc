<template>
  <div class="plan-alarms">
    <div class="alarms-header">
      <h2 class="section-title">Alarms ({{ alarmsList.length }})</h2>
    </div>

    <!-- Empty State -->
    <div v-if="alarmsList.length === 0" class="empty-state">
      <span class="empty-icon">🔔</span>
      <p class="empty-text">No alarms configured for this plan</p>
      <p class="empty-subtext">Alarms are created on individual sensors</p>
    </div>

    <!-- Alarms Table -->
    <div v-else class="alarms-table">
      <table>
        <thead>
          <tr>
            <th class="text-left">Alarm Name</th>
            <th class="text-left">Sensor</th>
            <th class="text-left">Condition</th>
            <th class="text-left">Status</th>
            <th class="text-right">Alerts</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alarm in alarmsList" :key="alarm.id" class="alarm-row">
            <td>
              <div class="alarm-info">
                <span class="alarm-icon">🔔</span>
                <span class="alarm-name">{{ alarm.name }}</span>
              </div>
            </td>
            <td>
              <span class="sensor-name">{{ getSensorName(alarm.sensor_id) }}</span>
            </td>
            <td>
              <span class="condition">{{ getCondition(alarm.name) }}</span>
            </td>
            <td>
              <span :class="['status-badge', 'status-active']">
                <span class="status-dot"></span>
                Active
              </span>
            </td>
            <td class="text-right">
              <span class="alert-count">{{ getAlertCount(alarm.id) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Alarm, Sensor } from '@/types'

const props = defineProps<{
  alarmsList: Alarm[]
  sensors: Sensor[]
}>()

const getSensorName = (sensorId: string): string => {
  const sensor = props.sensors.find(s => s.id === sensorId)
  return sensor?.name || 'Unknown Sensor'
}

const getCondition = (alarmName: string): string => {
  const lower = alarmName.toLowerCase()
  if (lower.includes('high temp')) return '> 30°C'
  if (lower.includes('low temp')) return '< 10°C'
  if (lower.includes('high humid')) return '> 80%'
  if (lower.includes('low humid')) return '< 40%'
  if (lower.includes('pressure')) return '< 900 hPa'
  return 'Custom condition'
}

const getAlertCount = (alarmId: string): number => {
  // Placeholder - would fetch from API
  return Math.floor(Math.random() * 3)
}
</script>

<style scoped>
.plan-alarms {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.alarms-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
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
  color: #111827;
  font-weight: 500;
}

.empty-subtext {
  font-size: 0.75rem;
  color: #6b7280;
}

.alarms-table {
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

.alarm-row {
  transition: background 0.15s ease;
}

.alarm-row:hover {
  background: #f9fafb;
}

td {
  padding: 1rem 1.5rem;
}

.alarm-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.alarm-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.alarm-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.sensor-name {
  font-size: 0.875rem;
  color: #6b7280;
}

.condition {
  font-size: 0.875rem;
  color: #111827;
  font-family: ui-monospace, SFMono-Regular, monospace;
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

.alert-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #991b1b;
  background: #fee2e2;
  border-radius: 0.25rem;
}

@media (max-width: 768px) {
  .alarms-table {
    overflow-x: auto;
  }

  table {
    min-width: 700px;
  }
}
</style>
