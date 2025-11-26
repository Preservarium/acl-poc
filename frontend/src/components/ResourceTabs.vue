<template>
  <div class="resource-tabs">
    <div class="tabs-header">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab', { active: activeTab === tab.id }]"
        @click="$emit('update:activeTab', tab.id)"
      >
        <span v-if="tab.icon" class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
        <span v-if="tab.count !== undefined" class="tab-count">{{ tab.count }}</span>
      </button>
    </div>
    <div class="tabs-content">
      <slot :name="activeTab"></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Tab {
  id: string;
  label: string;
  icon?: string;
  count?: number;
}

defineProps<{
  tabs: Tab[];
  activeTab: string;
}>();

defineEmits<{
  'update:activeTab': [tabId: string];
}>();
</script>

<style scoped>
.resource-tabs {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  overflow: hidden;
}

.tabs-header {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  background: #fafafa;
}

.tab {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 1.5rem;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.tab:hover {
  color: #374151;
  background: #f3f4f6;
}

.tab.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
  background: white;
}

.tab-icon {
  font-size: 1rem;
  line-height: 1;
}

.tab-label {
  white-space: nowrap;
}

.tab-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 9999px;
  background: #e5e7eb;
  color: #374151;
  line-height: 1;
}

.tab.active .tab-count {
  background: #dbeafe;
  color: #1e40af;
}

.tabs-content {
  padding: 1.5rem;
}

@media (max-width: 768px) {
  .tabs-header {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .tab {
    padding: 0.75rem 1rem;
    font-size: 0.8125rem;
  }

  .tabs-content {
    padding: 1rem;
  }
}
</style>
