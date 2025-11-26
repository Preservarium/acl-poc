<template>
  <div class="site-plans">
    <div class="plans-header">
      <h2 class="section-title">Plans</h2>
      <button
        @click="$emit('create-plan')"
        class="btn-primary"
      >
        + Add Plan
      </button>
    </div>

    <!-- Empty State -->
    <div v-if="plans.length === 0" class="empty-state">
      <span class="empty-icon">📋</span>
      <p class="empty-text">No plans created for this site yet</p>
      <button
        @click="$emit('create-plan')"
        class="btn-secondary"
      >
        Create First Plan
      </button>
    </div>

    <!-- Plans Table -->
    <div v-else class="plans-table">
      <table>
        <thead>
          <tr>
            <th class="text-left">Plan Name</th>
            <th class="text-center">Sensors</th>
            <th class="text-center">Brokers</th>
            <th class="text-center">Alarms</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="plan in plans" :key="plan.id" class="plan-row">
            <td>
              <div class="plan-info">
                <span class="plan-icon">📋</span>
                <div>
                  <div class="plan-name">{{ plan.name }}</div>
                  <div class="plan-meta">Created {{ formatDate(plan.created_at) }}</div>
                </div>
              </div>
            </td>
            <td class="text-center">
              <span class="count-badge">{{ getCounts(plan.id).sensors }}</span>
            </td>
            <td class="text-center">
              <span class="count-badge">{{ getCounts(plan.id).brokers }}</span>
            </td>
            <td class="text-center">
              <span class="count-badge">{{ getCounts(plan.id).alarms }}</span>
            </td>
            <td class="text-right">
              <button
                @click="$emit('view-plan', plan.id)"
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
import type { Plan } from '@/types'

const props = defineProps<{
  plans: Plan[]
  planCounts: Map<string, { sensors: number; brokers: number; alarms: number }>
}>()

defineEmits<{
  'create-plan': []
  'view-plan': [planId: string]
}>()

const getCounts = (planId: string) => {
  return props.planCounts.get(planId) || { sensors: 0, brokers: 0, alarms: 0 }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}
</script>

<style scoped>
.site-plans {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.plans-header {
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

.plans-table {
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

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

tbody tr {
  border-top: 1px solid #e5e7eb;
}

.plan-row {
  transition: background 0.15s ease;
}

.plan-row:hover {
  background: #f9fafb;
}

td {
  padding: 1rem 1.5rem;
}

.plan-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.plan-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.plan-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.plan-meta {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.125rem;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  background: #f3f4f6;
  border-radius: 0.25rem;
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
  .plans-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .plans-table {
    overflow-x: auto;
  }

  table {
    min-width: 600px;
  }
}
</style>
