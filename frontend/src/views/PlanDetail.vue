<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import ResourceTabs from '@/components/ResourceTabs.vue'
import PlanOverview from '@/components/plan/PlanOverview.vue'
import PlanSensors from '@/components/plan/PlanSensors.vue'
import PlanBrokers from '@/components/plan/PlanBrokers.vue'
import PlanAlarms from '@/components/plan/PlanAlarms.vue'
import PlanPermissions from '@/components/plan/PlanPermissions.vue'
import {
  fetchPlan,
  fetchSite,
  fetchSensors,
  fetchBrokers,
  fetchAlarms,
  createSensor,
  createBroker,
  updatePlan,
  deletePlan as deletePlanApi
} from '@/api/resources'
import { fetchResourcePermissions, revokePermission } from '@/api/permissions'
import type { Plan, Site, Sensor, Broker, Alarm, Permission } from '@/types'

const route = useRoute()
const router = useRouter()

const planId = computed(() => route.params.id as string)
const plan = ref<Plan | null>(null)
const site = ref<Site | null>(null)
const sensors = ref<Sensor[]>([])
const brokers = ref<Broker[]>([])
const alarms = ref<Alarm[]>([])
const permissions = ref<Permission[]>([])

const loading = ref(false)
const error = ref<string | null>(null)
const activeTab = ref<string>(route.params.tab as string || 'overview')

// Edit modal state
const showEditModal = ref(false)
const editForm = ref({
  name: '',
  description: ''
})
const editing = ref(false)
const editError = ref<string | null>(null)

// Create sensor modal state
const showCreateSensorModal = ref(false)
const sensorForm = ref({
  name: ''
})
const creatingSensor = ref(false)
const createSensorError = ref<string | null>(null)

// Create broker modal state
const showCreateBrokerModal = ref(false)
const brokerForm = ref({
  name: '',
  protocol: 'MQTT',
  host: '',
  port: ''
})
const creatingBroker = ref(false)
const createBrokerError = ref<string | null>(null)

const loadPlanDetails = async () => {
  loading.value = true
  error.value = null

  try {
    const planData = await fetchPlan(planId.value)
    plan.value = planData

    // Load related data
    const [siteData, sensorsData, brokersData, permissionsData] = await Promise.all([
      fetchSite(planData.site_id),
      fetchSensors(planId.value),
      fetchBrokers(planId.value),
      fetchResourcePermissions('plan', planId.value)
    ])

    site.value = siteData
    sensors.value = sensorsData
    brokers.value = brokersData
    permissions.value = permissionsData

    // Load alarms for all sensors
    const alarmPromises = sensorsData.map(sensor => fetchAlarms(sensor.id))
    const alarmsArrays = await Promise.all(alarmPromises)
    alarms.value = alarmsArrays.flat()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load plan details'
  } finally {
    loading.value = false
  }
}

const siteName = computed(() => site.value?.name || 'Unknown Site')

const openEditModal = () => {
  editForm.value = {
    name: plan.value?.name || '',
    description: ''
  }
  editError.value = null
  showEditModal.value = true
}

const handleEditPlan = async () => {
  if (!editForm.value.name.trim()) {
    editError.value = 'Plan name is required'
    return
  }

  editing.value = true
  editError.value = null

  try {
    await updatePlan(planId.value, {
      name: editForm.value.name,
      site_id: plan.value!.site_id
    })

    await loadPlanDetails()
    showEditModal.value = false
  } catch (err: any) {
    editError.value = err.response?.data?.detail || 'Failed to update plan'
  } finally {
    editing.value = false
  }
}

const deletePlan = async () => {
  if (!confirm(`Are you sure you want to delete plan "${plan.value?.name}"? This will also delete all associated sensors and brokers.`)) {
    return
  }

  try {
    await deletePlanApi(planId.value)
    router.push('/resources')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete plan'
  }
}

const openCreateSensorModal = () => {
  sensorForm.value = { name: '' }
  createSensorError.value = null
  showCreateSensorModal.value = true
}

const handleCreateSensor = async () => {
  if (!sensorForm.value.name.trim()) {
    createSensorError.value = 'Sensor name is required'
    return
  }

  creatingSensor.value = true
  createSensorError.value = null

  try {
    await createSensor({
      name: sensorForm.value.name,
      plan_id: planId.value
    })

    await loadPlanDetails()
    showCreateSensorModal.value = false
  } catch (err: any) {
    createSensorError.value = err.response?.data?.detail || 'Failed to create sensor'
  } finally {
    creatingSensor.value = false
  }
}

const openCreateBrokerModal = () => {
  brokerForm.value = {
    name: '',
    protocol: 'MQTT',
    host: '',
    port: ''
  }
  createBrokerError.value = null
  showCreateBrokerModal.value = true
}

const handleCreateBroker = async () => {
  if (!brokerForm.value.name.trim()) {
    createBrokerError.value = 'Broker name is required'
    return
  }

  if (!brokerForm.value.protocol.trim()) {
    createBrokerError.value = 'Protocol is required'
    return
  }

  creatingBroker.value = true
  createBrokerError.value = null

  try {
    await createBroker({
      name: brokerForm.value.name,
      protocol: brokerForm.value.protocol,
      plan_id: planId.value
    })

    await loadPlanDetails()
    showCreateBrokerModal.value = false
  } catch (err: any) {
    createBrokerError.value = err.response?.data?.detail || 'Failed to create broker'
  } finally {
    creatingBroker.value = false
  }
}

const handleRevokePermission = async (permissionId: string) => {
  if (!confirm('Are you sure you want to revoke this permission?')) {
    return
  }

  try {
    await revokePermission(permissionId)
    await loadPlanDetails()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to revoke permission'
  }
}

const navigateToSensor = (sensorId: string) => {
  router.push(`/sensors/${sensorId}`)
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const getAlarmCount = (sensor: Sensor) => {
  // This would need to be fetched from the API
  // For now, returning 0 as placeholder
  return 0
}

onMounted(() => {
  loadPlanDetails()
})
</script>

<template>
  <AppLayout>
    <div class="p-6">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading plan details...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="loadPlanDetails"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Plan Details -->
      <div v-else-if="plan">
        <!-- Header -->
        <div class="flex justify-between items-center mb-6">
          <div>
            <div class="text-sm text-gray-500 mb-1">
              <router-link to="/resources" class="hover:underline">Resources</router-link>
              <span class="mx-2">›</span>
              <span>{{ siteName }}</span>
              <span class="mx-2">›</span>
              <span>{{ plan.name }}</span>
            </div>
            <h1 class="text-2xl font-bold">📋 {{ plan.name }}</h1>
          </div>
          <div class="flex space-x-2">
            <button @click="openEditModal" class="px-4 py-2 border rounded hover:bg-gray-50">Edit</button>
            <button @click="deletePlan" class="px-4 py-2 border border-red-300 text-red-600 rounded hover:bg-red-50">Delete</button>
          </div>
        </div>

        <!-- Tabbed Content -->
        <ResourceTabs
          :tabs="[
            { id: 'overview', label: 'Overview' },
            { id: 'sensors', label: 'Sensors', count: sensors.length },
            { id: 'brokers', label: 'Brokers', count: brokers.length },
            { id: 'alarms', label: 'Alarms', count: alarms.length },
            { id: 'permissions', label: 'Permissions', icon: '🔐' }
          ]"
          v-model:activeTab="activeTab"
        >
          <template #overview>
            <PlanOverview
              :plan="plan"
              :site-name="siteName"
              :sensors-count="sensors.length"
              :brokers-count="brokers.length"
              :alarms-count="alarms.length"
              :alerts-count="0"
              :active-sensors-count="sensors.length"
              :online-brokers-count="brokers.length"
              :active-alarms-count="alarms.length"
              :unacknowledged-alerts-count="0"
            />
          </template>
          <template #sensors>
            <PlanSensors
              :sensors="sensors"
              @create-sensor="openCreateSensorModal"
              @view-sensor="navigateToSensor"
            />
          </template>
          <template #brokers>
            <PlanBrokers
              :brokers="brokers"
              @create-broker="openCreateBrokerModal"
            />
          </template>
          <template #alarms>
            <PlanAlarms
              :alarms-list="alarms"
              :sensors="sensors"
            />
          </template>
          <template #permissions>
            <PlanPermissions
              :plan-id="planId"
            />
          </template>
        </ResourceTabs>
      </div>

      <!-- Edit Plan Modal -->
      <Transition name="modal">
        <div
          v-if="showEditModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          @click.self="showEditModal = false"
        >
          <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <!-- Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 class="text-xl font-bold text-gray-800">Edit Plan</h2>
              <button
                @click="showEditModal = false"
                class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <!-- Content -->
            <div class="p-6">
              <!-- Error Message -->
              <div v-if="editError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {{ editError }}
              </div>

              <form @submit.prevent="handleEditPlan" class="space-y-4">
                <!-- Name Field -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Plan Name
                  </label>
                  <input
                    v-model="editForm.name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter plan name"
                  />
                </div>

                <!-- Buttons -->
                <div class="flex justify-end gap-3">
                  <button
                    type="button"
                    @click="showEditModal = false"
                    class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    :disabled="editing"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {{ editing ? 'Saving...' : 'Save' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Create Sensor Modal -->
      <Transition name="modal">
        <div
          v-if="showCreateSensorModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          @click.self="showCreateSensorModal = false"
        >
          <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <!-- Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 class="text-xl font-bold text-gray-800">Create New Sensor</h2>
              <button
                @click="showCreateSensorModal = false"
                class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <!-- Content -->
            <div class="p-6">
              <!-- Error Message -->
              <div v-if="createSensorError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {{ createSensorError }}
              </div>

              <form @submit.prevent="handleCreateSensor" class="space-y-4">
                <!-- Name Field -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Sensor Name
                  </label>
                  <input
                    v-model="sensorForm.name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter sensor name"
                  />
                </div>

                <!-- Buttons -->
                <div class="flex justify-end gap-3">
                  <button
                    type="button"
                    @click="showCreateSensorModal = false"
                    class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    :disabled="creatingSensor"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {{ creatingSensor ? 'Creating...' : 'Create' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Create Broker Modal -->
      <Transition name="modal">
        <div
          v-if="showCreateBrokerModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          @click.self="showCreateBrokerModal = false"
        >
          <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <!-- Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 class="text-xl font-bold text-gray-800">Create New Broker</h2>
              <button
                @click="showCreateBrokerModal = false"
                class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <!-- Content -->
            <div class="p-6">
              <!-- Error Message -->
              <div v-if="createBrokerError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {{ createBrokerError }}
              </div>

              <form @submit.prevent="handleCreateBroker" class="space-y-4">
                <!-- Name Field -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Broker Name
                  </label>
                  <input
                    v-model="brokerForm.name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter broker name"
                  />
                </div>

                <!-- Protocol Field -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Protocol
                  </label>
                  <select
                    v-model="brokerForm.protocol"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="MQTT">MQTT</option>
                    <option value="HTTP">HTTP</option>
                    <option value="CoAP">CoAP</option>
                    <option value="AMQP">AMQP</option>
                  </select>
                </div>

                <!-- Buttons -->
                <div class="flex justify-end gap-3">
                  <button
                    type="button"
                    @click="showCreateBrokerModal = false"
                    class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    :disabled="creatingBroker"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {{ creatingBroker ? 'Creating...' : 'Create' }}
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
