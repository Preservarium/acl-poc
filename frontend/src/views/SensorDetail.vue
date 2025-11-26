<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import PermissionList from '@/components/PermissionList.vue'
import FieldPermissionBadge from '@/components/FieldPermissionBadge.vue'
import UserPermissionSummary from '@/components/UserPermissionSummary.vue'
import { fetchSensor, fetchPlan, fetchAlarms, createAlarm, deleteAlarm } from '@/api/resources'
import { fetchResourcePermissions, revokePermission } from '@/api/permissions'
import type { Sensor, Plan, Alarm, Permission } from '@/types'

const route = useRoute()
const router = useRouter()

const sensorId = computed(() => route.params.id as string)
const sensor = ref<Sensor | null>(null)
const plan = ref<Plan | null>(null)
const alarms = ref<Alarm[]>([])
const permissions = ref<Permission[]>([])

const loading = ref(false)
const error = ref<string | null>(null)

// Tab state
const activeTab = ref<'overview' | 'fields' | 'alarms' | 'permissions'>('overview')

// Field-level permissions
const writableFields = ref<string[]>([])
const allFields = ['field_a', 'field_b', 'field_c', 'field_d', 'field_e']

// Field values (mock data for display)
const fieldValues = ref<Record<string, string>>({
  field_a: '23.5',
  field_b: '45.2',
  field_c: '67.8',
  field_d: '2024-01-15',
  field_e: 'Active'
})

// Field display names
const fieldLabels: Record<string, string> = {
  field_a: 'Temperature',
  field_b: 'Humidity',
  field_c: 'Pressure',
  field_d: 'Calibration Date',
  field_e: 'Status'
}

// Computed property for editable fields to show in the banner
const editableFields = computed(() => {
  return writableFields.value.length > 0 ? writableFields.value : []
})

const readonlyFields = computed(() => {
  return allFields.filter(field => !writableFields.value.includes(field))
})

// Create alarm modal state
const showCreateAlarmModal = ref(false)
const alarmForm = ref({
  name: ''
})
const creatingAlarm = ref(false)
const createAlarmError = ref<string | null>(null)

const loadSensorDetails = async () => {
  loading.value = true
  error.value = null

  try {
    // Fetch sensor with permission metadata
    const sensorData = await fetchSensor(sensorId.value, true)
    sensor.value = sensorData

    // Load related data
    const [planData, alarmsData, permissionsData] = await Promise.all([
      fetchPlan(sensorData.plan_id),
      fetchAlarms(sensorId.value),
      fetchResourcePermissions('sensor', sensorId.value)
    ])

    plan.value = planData
    alarms.value = alarmsData
    permissions.value = permissionsData

    // Extract writable fields from _permissions metadata
    if (sensorData._permissions) {
      if (sensorData._permissions.can_write) {
        // If writable_fields is null/undefined, all fields are writable
        // If it's an array, only those fields are writable
        if (sensorData._permissions.writable_fields === null ||
            sensorData._permissions.writable_fields === undefined) {
          writableFields.value = allFields
        } else {
          writableFields.value = sensorData._permissions.writable_fields
        }
      } else {
        writableFields.value = []
      }
    } else {
      // Fallback: no permission metadata available
      writableFields.value = []
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load sensor details'
  } finally {
    loading.value = false
  }
}

const isFieldEditable = (field: string) => {
  return writableFields.value.includes(field)
}

const openCreateAlarmModal = () => {
  alarmForm.value = { name: '' }
  createAlarmError.value = null
  showCreateAlarmModal.value = true
}

const handleCreateAlarm = async () => {
  if (!alarmForm.value.name.trim()) {
    createAlarmError.value = 'Alarm name is required'
    return
  }

  creatingAlarm.value = true
  createAlarmError.value = null

  try {
    await createAlarm({
      name: alarmForm.value.name,
      sensor_id: sensorId.value
    })

    await loadSensorDetails()
    showCreateAlarmModal.value = false
  } catch (err: any) {
    createAlarmError.value = err.response?.data?.detail || 'Failed to create alarm'
  } finally {
    creatingAlarm.value = false
  }
}

const handleDeleteAlarm = async (alarmId: string) => {
  if (!confirm('Are you sure you want to delete this alarm?')) {
    return
  }

  try {
    await deleteAlarm(alarmId)
    await loadSensorDetails()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete alarm'
  }
}

const handleRevokePermission = async (permissionId: string) => {
  if (!confirm('Are you sure you want to revoke this permission?')) {
    return
  }

  try {
    await revokePermission(permissionId)
    await loadSensorDetails()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to revoke permission'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

onMounted(() => {
  loadSensorDetails()
})
</script>

<template>
  <AppLayout>
    <div class="container mx-auto px-4 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading sensor details...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="loadSensorDetails"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Sensor Details -->
      <div v-else-if="sensor" class="space-y-6">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <button
                @click="router.back()"
                class="text-gray-400 hover:text-gray-600 transition-colors"
              >
                ← Back
              </button>
              <span class="text-3xl">📡</span>
              <h1 class="text-3xl font-bold text-gray-800">{{ sensor.name }}</h1>
            </div>
          </div>

          <!-- Tabs -->
          <div class="border-b border-gray-200 mb-4">
            <nav class="-mb-px flex space-x-8">
              <button
                @click="activeTab = 'overview'"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                  activeTab === 'overview'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                Overview
              </button>
              <button
                @click="activeTab = 'fields'"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                  activeTab === 'fields'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                Fields
              </button>
              <button
                @click="activeTab = 'alarms'"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                  activeTab === 'alarms'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                Alarms
              </button>
              <button
                @click="activeTab = 'permissions'"
                :class="[
                  'py-2 px-1 border-b-2 font-medium text-sm transition-colors',
                  activeTab === 'permissions'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]"
              >
                Permissions
              </button>
            </nav>
          </div>

          <!-- Overview Tab Content -->
          <div v-if="activeTab === 'overview'">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-500">Plan:</span>
                <span class="ml-2 text-gray-800">{{ plan?.name }}</span>
              </div>
              <div>
                <span class="text-gray-500">Created By:</span>
                <span class="ml-2 text-gray-800">{{ sensor.created_by }}</span>
              </div>
              <div>
                <span class="text-gray-500">Created:</span>
                <span class="ml-2 text-gray-800">{{ formatDate(sensor.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Fields Section -->
        <div v-if="activeTab === 'fields'" class="space-y-6">
          <!-- User Permission Summary -->
          <UserPermissionSummary
            resource-type="sensor"
            :resource-id="sensorId"
          />

          <!-- Fields Display -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">Sensor Fields</h2>

            <!-- Info Banner -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div class="flex items-start">
                <span class="text-blue-600 mr-2 text-lg">ℹ️</span>
                <div class="flex-1">
                  <span v-if="editableFields.length > 0" class="text-sm text-blue-800">
                    You can edit fields: <strong>{{ editableFields.map(f => fieldLabels[f] || f).join(', ') }}</strong>.
                    <br class="mb-1">
                    Other fields are read-only for your role.
                  </span>
                  <span v-else class="text-sm text-blue-800">
                    All fields are read-only for your role.
                  </span>
                </div>
              </div>
            </div>

            <!-- Field List -->
            <div class="space-y-4">
              <div
                v-for="field in allFields"
                :key="field"
                class="border border-gray-200 rounded-lg overflow-hidden"
              >
                <!-- Field Header -->
                <div class="bg-gray-50 px-4 py-2 border-b border-gray-200">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <span class="text-sm font-semibold text-gray-700">
                        {{ fieldLabels[field] || field }}
                      </span>
                      <span class="text-xs text-gray-500">({{ field }})</span>
                    </div>
                    <FieldPermissionBadge :editable="isFieldEditable(field)" size="sm" />
                  </div>
                </div>

                <!-- Field Value -->
                <div class="p-4">
                  <input
                    v-model="fieldValues[field]"
                    type="text"
                    :disabled="!isFieldEditable(field)"
                    :class="[
                      'w-full px-3 py-2 border rounded-md transition-colors',
                      isFieldEditable(field)
                        ? 'border-gray-300 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                        : 'border-gray-200 bg-gray-100 text-gray-600 cursor-not-allowed'
                    ]"
                  />
                  <p v-if="!isFieldEditable(field)" class="mt-2 text-xs text-gray-500 flex items-center gap-1">
                    <span>🔒</span>
                    <span>This field is read-only based on your permissions</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Alarms Section -->
        <div v-if="activeTab === 'alarms'" class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-bold text-gray-800">Alarms</h2>
            <button
              @click="openCreateAlarmModal"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              + Create Alarm
            </button>
          </div>

          <!-- Empty State -->
          <div v-if="alarms.length === 0" class="text-center py-8 text-gray-500 border border-gray-200 rounded-lg">
            No alarms configured for this sensor
          </div>

          <!-- Alarms List -->
          <div v-else class="space-y-2">
            <div
              v-for="alarm in alarms"
              :key="alarm.id"
              class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div class="flex items-center gap-3">
                <span class="text-2xl">🔔</span>
                <div>
                  <div class="font-medium text-gray-800">{{ alarm.name }}</div>
                  <div class="text-xs text-gray-500">
                    Created by {{ alarm.created_by }} on {{ formatDate(alarm.created_at) }}
                  </div>
                </div>
              </div>
              <button
                @click="handleDeleteAlarm(alarm.id)"
                class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>

        <!-- Permissions Section -->
        <div v-if="activeTab === 'permissions'" class="bg-white rounded-lg shadow-md p-6">
          <h2 class="text-2xl font-bold text-gray-800 mb-4">Permissions</h2>
          <p class="text-gray-600 mb-4">Who has access to this sensor:</p>

          <PermissionList
            :permissions="permissions"
            :loading="false"
            @revoke="handleRevokePermission"
          />
        </div>
      </div>

      <!-- Create Alarm Modal -->
      <Transition name="modal">
        <div
          v-if="showCreateAlarmModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          @click.self="showCreateAlarmModal = false"
        >
          <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <!-- Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 class="text-xl font-bold text-gray-800">Create New Alarm</h2>
              <button
                @click="showCreateAlarmModal = false"
                class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <!-- Content -->
            <div class="p-6">
              <!-- Error Message -->
              <div v-if="createAlarmError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {{ createAlarmError }}
              </div>

              <form @submit.prevent="handleCreateAlarm" class="space-y-4">
                <!-- Name Field -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Alarm Name
                  </label>
                  <input
                    v-model="alarmForm.name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter alarm name"
                  />
                </div>

                <!-- Buttons -->
                <div class="flex justify-end gap-3">
                  <button
                    type="button"
                    @click="showCreateAlarmModal = false"
                    class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    :disabled="creatingAlarm"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {{ creatingAlarm ? 'Creating...' : 'Create' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </AppLayout>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.9);
}
</style>
