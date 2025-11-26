<template>
  <div class="alert-card bg-white rounded-lg shadow p-4"
       :class="{
         'border-l-4 border-blue-500': alert.severity === 'info',
         'border-l-4 border-yellow-500': alert.severity === 'warning',
         'border-l-4 border-red-500': alert.severity === 'critical'
       }">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3 flex-1">
        <span class="text-2xl">{{ getSeverityIcon(alert.severity) }}</span>
        <div class="flex-1">
          <div class="flex items-center space-x-2">
            <h3 class="font-semibold text-gray-900">{{ alert.message }}</h3>
            <span class="px-2 py-1 text-xs font-semibold rounded-full"
                  :class="{
                    'bg-blue-100 text-blue-800': alert.severity === 'info',
                    'bg-yellow-100 text-yellow-800': alert.severity === 'warning',
                    'bg-red-100 text-red-800': alert.severity === 'critical'
                  }">
              {{ alert.severity }}
            </span>
          </div>
          <p class="text-sm text-gray-500 mt-1">
            Triggered: {{ formatDate(alert.triggered_at) }}
          </p>
          <p v-if="alert.acknowledged" class="text-xs text-green-600 mt-1">
            ✓ Acknowledged
          </p>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <button
          v-if="!alert.acknowledged && canAcknowledge"
          @click="$emit('acknowledge', alert)"
          class="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
        >
          Acknowledge
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Alert {
  id: string;
  message: string;
  severity: string;
  triggered_at: string;
  acknowledged: boolean;
  alarm_id: string;
}

defineProps<{
  alert: Alert;
  canAcknowledge?: boolean;
}>();

defineEmits<{
  (e: 'acknowledge', alert: Alert): void;
}>();

const getSeverityIcon = (severity: string): string => {
  const icons: Record<string, string> = {
    'info': 'ℹ️',
    'warning': '⚠️',
    'critical': '🚨'
  };
  return icons[severity] || '📢';
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString();
};
</script>
