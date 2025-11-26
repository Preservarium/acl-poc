<template>
  <div class="stats-card">
    <div class="stats-icon">{{ icon }}</div>
    <div class="stats-content">
      <div class="stats-value">{{ value }}</div>
      <div class="stats-label">{{ label }}</div>
      <div v-if="subtitle" class="stats-subtitle">{{ subtitle }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string;
  value: number | string;
  label: string;
  subtitle?: string;
}>();
</script>

<style scoped>
.stats-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  transition: all 0.15s ease;
}

.stats-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}

.stats-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 3rem;
  height: 3rem;
  font-size: 2rem;
  background: #f3f4f6;
  border-radius: 0.5rem;
  flex-shrink: 0;
}

.stats-content {
  flex: 1;
  min-width: 0;
}

.stats-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
}

.stats-label {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.stats-subtitle {
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #9ca3af;
}

@media (max-width: 640px) {
  .stats-card {
    padding: 1rem;
  }

  .stats-icon {
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1.5rem;
  }

  .stats-value {
    font-size: 1.5rem;
  }

  .stats-label {
    font-size: 0.8125rem;
  }
}
</style>
