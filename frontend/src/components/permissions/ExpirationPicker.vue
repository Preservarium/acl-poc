<script setup lang="ts">
import { ref, watch, computed } from 'vue'

const props = defineProps<{
  modelValue: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

// Internal state for "enable expiration" checkbox
const enableExpiration = ref(!!props.modelValue)

// Internal state for expiration date/time
const expirationDate = ref(props.modelValue || '')

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    enableExpiration.value = true
    expirationDate.value = newValue
  } else {
    enableExpiration.value = false
    expirationDate.value = ''
  }
})

// Toggle expiration checkbox
const toggleExpiration = () => {
  if (enableExpiration.value) {
    // Set a default date to 30 days from now
    const defaultDate = new Date()
    defaultDate.setDate(defaultDate.getDate() + 30)
    expirationDate.value = formatDateForInput(defaultDate)
    emit('update:modelValue', expirationDate.value)
  } else {
    // Disabled - clear the value
    expirationDate.value = ''
    emit('update:modelValue', null)
  }
}

// Watch expiration date and emit changes
watch(expirationDate, (newDate) => {
  if (enableExpiration.value && newDate) {
    emit('update:modelValue', newDate)
  }
})

// Format date for datetime-local input
const formatDateForInput = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

// Get minimum date (current date/time)
const minDate = computed(() => {
  return formatDateForInput(new Date())
})

// Format display date
const displayDate = computed(() => {
  if (!expirationDate.value) return ''
  try {
    const date = new Date(expirationDate.value)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return expirationDate.value
  }
})
</script>

<template>
  <div class="expiration-picker">
    <!-- Enable Expiration Checkbox -->
    <div class="checkbox-wrapper">
      <label class="checkbox-label">
        <input
          type="checkbox"
          v-model="enableExpiration"
          @change="toggleExpiration"
          class="checkbox-input"
        />
        <span class="checkbox-text">Set expiration date</span>
      </label>
    </div>

    <!-- Date/Time Picker -->
    <div v-if="enableExpiration" class="date-picker-wrapper">
      <div class="date-input-container">
        <input
          type="datetime-local"
          v-model="expirationDate"
          :min="minDate"
          class="date-input"
          required
        />
        <span class="calendar-icon">📅</span>
      </div>

      <div v-if="displayDate" class="date-display">
        Expires: {{ displayDate }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.expiration-picker {
  margin-top: 0.5rem;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  user-select: none;
}

.checkbox-input {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
  accent-color: #4f46e5;
}

.checkbox-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.date-picker-wrapper {
  margin-top: 0.75rem;
  margin-left: 1.5rem;
  padding: 0.75rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
}

.date-input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.date-input {
  width: 100%;
  padding: 0.5rem 2.5rem 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  color: #374151;
  background-color: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.date-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.calendar-icon {
  position: absolute;
  right: 0.75rem;
  font-size: 1.25rem;
  pointer-events: none;
}

.date-display {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
}
</style>
