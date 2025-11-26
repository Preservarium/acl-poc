<template>
  <div class="alarm-card bg-white rounded-lg shadow p-4"
       :class="{
         'border-l-4 border-green-500': alarm.active,
         'border-l-4 border-gray-400': !alarm.active
       }">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-2xl">{{ alarm.active ? '🔔' : '🔕' }}</span>
        <div>
          <h3 class="font-semibold text-gray-900">{{ alarm.name }}</h3>
          <p class="text-sm text-gray-500">
            Threshold: {{ alarm.threshold }} ({{ getConditionLabel(alarm.condition) }})
          </p>
          <p v-if="alertCount !== undefined" class="text-xs text-gray-400 mt-1">
            {{ alertCount }} alert{{ alertCount !== 1 ? 's' : '' }}
          </p>
        </div>
      </div>
      <div class="flex flex-col items-end space-y-2">
        <div class="flex items-center space-x-2">
          <span class="px-2 py-1 text-xs font-semibold rounded-full"
                :class="{
                  'bg-green-100 text-green-800': alarm.active,
                  'bg-gray-100 text-gray-800': !alarm.active
                }">
            {{ alarm.active ? 'Active' : 'Inactive' }}
          </span>
        </div>
        <div class="flex items-center space-x-2">
          <button v-if="canEdit" @click="$emit('edit', alarm)" class="text-blue-600 hover:text-blue-800 text-sm">
            Edit
          </button>
          <button v-if="canDelete" @click="$emit('delete', alarm)" class="text-red-600 hover:text-red-800 text-sm">
            Delete
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Alarm {
  id: string;
  name: string;
  threshold: number;
  condition: string;
  active: boolean;
  sensor_id: string;
}

defineProps<{
  alarm: Alarm;
  alertCount?: number;
  canEdit?: boolean;
  canDelete?: boolean;
}>();

defineEmits<{
  (e: 'edit', alarm: Alarm): void;
  (e: 'delete', alarm: Alarm): void;
}>();

const getConditionLabel = (condition: string): string => {
  const labels: Record<string, string> = {
    'gt': '>',
    'lt': '<',
    'eq': '=',
    'gte': '>=',
    'lte': '<='
  };
  return labels[condition] || condition;
};
</script>
