<script setup lang="ts">
import { ref, watch, computed } from 'vue'

const props = defineProps<{
  availableFields: string[]
  modelValue: string[] | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string[] | null]
}>()

// Internal state for "all fields" checkbox
const allFields = ref(props.modelValue === null)

// Internal state for selected fields
const selectedFields = ref<string[]>(
  props.modelValue === null ? [] : (props.modelValue || [])
)

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  if (newValue === null) {
    allFields.value = true
    selectedFields.value = []
  } else {
    allFields.value = false
    selectedFields.value = [...newValue]
  }
})

// Toggle all fields checkbox
const toggleAllFields = () => {
  if (allFields.value) {
    // All fields selected - emit null
    selectedFields.value = []
    emit('update:modelValue', null)
  } else {
    // All fields deselected - emit empty array or current selection
    emit('update:modelValue', selectedFields.value.length > 0 ? selectedFields.value : [])
  }
}

// Watch selected fields and emit changes
watch(selectedFields, (newFields) => {
  if (!allFields.value) {
    emit('update:modelValue', newFields.length > 0 ? newFields : null)
  }
}, { deep: true })

// Computed property to check if any fields are available
const hasFields = computed(() => props.availableFields && props.availableFields.length > 0)
</script>

<template>
  <div class="field-selector">
    <label class="block text-sm font-medium text-gray-700 mb-2">
      Field Restrictions
    </label>

    <div v-if="!hasFields" class="text-sm text-gray-500 italic">
      No fields available for this resource type
    </div>

    <div v-else>
      <!-- All Fields Checkbox -->
      <div class="flex items-center mb-3">
        <input
          type="checkbox"
          v-model="allFields"
          @change="toggleAllFields"
          id="all-fields-checkbox"
          class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
        />
        <label for="all-fields-checkbox" class="ml-2 text-sm font-medium text-gray-700">
          All fields
        </label>
      </div>

      <!-- Individual Field Checkboxes -->
      <div v-if="!allFields" class="grid grid-cols-3 gap-2">
        <label
          v-for="field in availableFields"
          :key="field"
          class="flex items-center"
        >
          <input
            type="checkbox"
            :value="field"
            v-model="selectedFields"
            class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span class="ml-2 text-sm text-gray-700">{{ field }}</span>
        </label>
      </div>

      <!-- Selected Count -->
      <div v-if="!allFields && selectedFields.length > 0" class="mt-2 text-xs text-gray-500">
        {{ selectedFields.length }} field{{ selectedFields.length !== 1 ? 's' : '' }} selected
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Optional: Add hover effects for better UX */
label {
  cursor: pointer;
  user-select: none;
}

label:hover {
  opacity: 0.8;
}
</style>
