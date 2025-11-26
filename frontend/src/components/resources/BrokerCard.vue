<template>
  <div class="broker-card bg-white rounded-lg shadow p-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <span class="text-2xl">📶</span>
        <div>
          <h3 class="font-semibold text-gray-900">{{ broker.name }}</h3>
          <p class="text-sm text-gray-500">{{ broker.protocol }} - {{ broker.host }}:{{ broker.port }}</p>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <button v-if="canEdit" @click="$emit('edit', broker)" class="text-blue-600 hover:text-blue-800">
          Edit
        </button>
        <button v-if="canDelete" @click="$emit('delete', broker)" class="text-red-600 hover:text-red-800">
          Delete
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Broker {
  id: string;
  name: string;
  protocol: string;
  host: string;
  port: number;
  plan_id: string;
}

defineProps<{
  broker: Broker;
  canEdit?: boolean;
  canDelete?: boolean;
}>();

defineEmits<{
  (e: 'edit', broker: Broker): void;
  (e: 'delete', broker: Broker): void;
}>();
</script>
