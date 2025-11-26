<template>
  <div class="dashboard-card bg-white rounded-lg shadow p-4 hover:shadow-lg transition-shadow">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3 flex-1">
        <span class="text-2xl">📊</span>
        <div class="flex-1">
          <h3 class="font-semibold text-gray-900">{{ dashboard.name }}</h3>
          <p class="text-sm text-gray-500 mt-1">
            Created by: {{ creatorName || dashboard.created_by }}
          </p>
          <p class="text-xs text-gray-400 mt-1">
            {{ formatDate(dashboard.created_at) }}
          </p>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <button v-if="canEdit" @click="$emit('edit', dashboard)" class="text-blue-600 hover:text-blue-800">
          Edit
        </button>
        <button v-if="canDelete" @click="$emit('delete', dashboard)" class="text-red-600 hover:text-red-800">
          Delete
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Dashboard {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
  config?: Record<string, any>;
}

defineProps<{
  dashboard: Dashboard;
  creatorName?: string;
  canEdit?: boolean;
  canDelete?: boolean;
}>();

defineEmits<{
  (e: 'edit', dashboard: Dashboard): void;
  (e: 'delete', dashboard: Dashboard): void;
}>();

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString();
};
</script>
