<template>
  <div class="plan-overview">
    <div class="overview-section">
      <h2 class="section-title">Plan Information</h2>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Name</span>
          <div class="info-value">{{ plan?.name }}</div>
        </div>
        <div class="info-item">
          <span class="info-label">Parent Site</span>
          <div class="info-value">{{ siteName }}</div>
        </div>
        <div class="info-item">
          <span class="info-label">Created By</span>
          <div class="info-value">{{ plan?.created_by }}</div>
        </div>
        <div class="info-item">
          <span class="info-label">Created At</span>
          <div class="info-value">{{ formatDate(plan?.created_at) }}</div>
        </div>
      </div>
    </div>

    <div class="overview-section">
      <h2 class="section-title">Quick Stats</h2>
      <div class="stats-grid">
        <StatsCard
          icon="📡"
          :value="sensorsCount"
          label="Sensors"
          :subtitle="`${activeSensorsCount} active`"
        />
        <StatsCard
          icon="🔌"
          :value="brokersCount"
          label="Brokers"
          :subtitle="`${onlineBrokersCount} online`"
        />
        <StatsCard
          icon="🔔"
          :value="alarmsCount"
          label="Alarms"
          :subtitle="`${activeAlarmsCount} active`"
        />
        <StatsCard
          icon="⚠️"
          :value="alertsCount"
          label="Alerts"
          :subtitle="unacknowledgedAlertsCount > 0 ? `${unacknowledgedAlertsCount} unack` : 'All clear'"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import StatsCard from '@/components/StatsCard.vue'
import type { Plan } from '@/types'

const props = defineProps<{
  plan: Plan | null
  siteName: string
  sensorsCount: number
  brokersCount: number
  alarmsCount: number
  alertsCount: number
  activeSensorsCount?: number
  onlineBrokersCount?: number
  activeAlarmsCount?: number
  unacknowledgedAlertsCount?: number
}>()

const formatDate = (dateString?: string) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}
</script>

<style scoped>
.plan-overview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.overview-section {
  background: white;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.info-value {
  font-size: 1rem;
  font-weight: 500;
  color: #111827;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
