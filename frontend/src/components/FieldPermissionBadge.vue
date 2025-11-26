<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  editable: boolean
  size?: 'sm' | 'md' | 'lg'
}>()

const sizeClasses = computed(() => {
  switch (props.size || 'md') {
    case 'sm':
      return 'text-xs px-2 py-0.5'
    case 'md':
      return 'text-sm px-2.5 py-1'
    case 'lg':
      return 'text-base px-3 py-1.5'
    default:
      return 'text-sm px-2.5 py-1'
  }
})

const badgeClasses = computed(() => {
  const baseClasses = 'inline-flex items-center gap-1 rounded-md font-medium'
  const colorClasses = props.editable
    ? 'bg-green-100 text-green-800 border border-green-200'
    : 'bg-gray-100 text-gray-600 border border-gray-300'

  return `${baseClasses} ${colorClasses} ${sizeClasses.value}`
})
</script>

<template>
  <span :class="badgeClasses">
    <span class="text-base leading-none">{{ editable ? '✏️' : '🔒' }}</span>
    <span>{{ editable ? 'Editable' : 'Read-only' }}</span>
  </span>
</template>

<style scoped>
/* Ensure emoji renders consistently */
span {
  vertical-align: middle;
}
</style>
