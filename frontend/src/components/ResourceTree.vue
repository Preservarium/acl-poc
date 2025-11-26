<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { fetchSites, fetchPlans, fetchSensors, fetchAlarms, fetchAlerts, fetchBrokers } from '@/api/resources'
import type { Site, Plan, Sensor, Alarm, Alert, Broker } from '@/types'

interface TreeNode {
  id: string
  name: string
  type: 'site' | 'plan' | 'sensor' | 'alarm' | 'alert' | 'broker'
  expanded: boolean
  children?: TreeNode[]
  parent_id?: string
  severity?: string // for alerts
  protocol?: string // for brokers
  message?: string // for alerts
}

const emit = defineEmits<{
  'manage-permissions': [type: string, id: string, name: string]
  'edit-resource': [type: string, id: string]
  'create-site': []
}>()

const props = defineProps<{
  userIsAdmin: boolean
}>()

const sites = ref<Site[]>([])
const plans = ref<Plan[]>([])
const sensors = ref<Sensor[]>([])
const alarms = ref<Alarm[]>([])
const alerts = ref<Alert[]>([])
const brokers = ref<Broker[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Track expanded state
const expandedNodes = ref<Set<string>>(new Set())

const loadData = async () => {
  loading.value = true
  error.value = null
  try {
    const [sitesData, plansData, sensorsData, alarmsData, alertsData, brokersData] = await Promise.all([
      fetchSites(),
      fetchPlans(),
      fetchSensors(),
      fetchAlarms(),
      fetchAlerts(),
      fetchBrokers()
    ])
    sites.value = sitesData
    plans.value = plansData
    sensors.value = sensorsData
    alarms.value = alarmsData
    alerts.value = alertsData
    brokers.value = brokersData
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load resources'
  } finally {
    loading.value = false
  }
}

const toggleNode = (nodeId: string) => {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
}

const isExpanded = (nodeId: string) => {
  return expandedNodes.value.has(nodeId)
}

// Build hierarchical tree structure
const treeData = computed(() => {
  return sites.value.map(site => {
    const sitePlans = plans.value.filter(plan => plan.site_id === site.id)
    return {
      id: site.id,
      name: site.name,
      type: 'site' as const,
      expanded: isExpanded(site.id),
      children: sitePlans.map(plan => {
        const planSensors = sensors.value.filter(sensor => sensor.plan_id === plan.id)
        const planBrokers = brokers.value.filter(broker => broker.plan_id === plan.id)

        // Combine sensors and brokers as plan children
        const planChildren: TreeNode[] = []

        // Add sensors with their alarms and alerts
        planSensors.forEach(sensor => {
          const sensorAlarms = alarms.value.filter(alarm => alarm.sensor_id === sensor.id)
          planChildren.push({
            id: sensor.id,
            name: sensor.name,
            type: 'sensor' as const,
            expanded: isExpanded(sensor.id),
            parent_id: plan.id,
            children: sensorAlarms.map(alarm => {
              const alarmAlerts = alerts.value.filter(alert => alert.alarm_id === alarm.id)
              return {
                id: alarm.id,
                name: alarm.name,
                type: 'alarm' as const,
                expanded: isExpanded(alarm.id),
                parent_id: sensor.id,
                children: alarmAlerts.map(alert => ({
                  id: alert.id,
                  name: alert.message,
                  type: 'alert' as const,
                  expanded: false,
                  parent_id: alarm.id,
                  severity: alert.severity,
                  message: alert.message
                }))
              }
            })
          })
        })

        // Add brokers
        planBrokers.forEach(broker => {
          planChildren.push({
            id: broker.id,
            name: broker.name,
            type: 'broker' as const,
            expanded: false,
            parent_id: plan.id,
            protocol: broker.protocol
          })
        })

        return {
          id: plan.id,
          name: plan.name,
          type: 'plan' as const,
          expanded: isExpanded(plan.id),
          parent_id: site.id,
          children: planChildren
        }
      })
    }
  })
})

const getIcon = (type: string) => {
  switch (type) {
    case 'site': return '🏭'
    case 'plan': return '📋'
    case 'sensor': return '📡'
    case 'alarm': return '🔔'
    case 'alert': return '⚠️'
    case 'broker': return '📶'
    default: return '📄'
  }
}

onMounted(() => {
  loadData()
})

defineExpose({ loadData })
</script>

<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-2xl font-bold text-gray-800">Resources</h2>
      <button
        v-if="userIsAdmin"
        @click="emit('create-site')"
        class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2"
      >
        <span>+</span>
        <span>Site</span>
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-8 text-gray-500">
      Loading resources...
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-8 text-red-600">
      {{ error }}
      <button @click="loadData" class="ml-2 text-blue-600 hover:underline">
        Retry
      </button>
    </div>

    <!-- Tree Display -->
    <div v-else class="space-y-2">
      <!-- Empty State -->
      <div v-if="treeData.length === 0" class="text-center py-8 text-gray-500">
        No resources yet. Create a site to get started.
      </div>

      <!-- Site Level -->
      <div v-for="site in treeData" :key="site.id" class="border-l-2 border-gray-200 pl-2">
        <div class="flex items-center gap-2 py-2 hover:bg-gray-50 rounded px-2 group">
          <!-- Expand/Collapse Button -->
          <button
            v-if="site.children && site.children.length > 0"
            @click="toggleNode(site.id)"
            class="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-gray-800"
          >
            {{ site.expanded ? '▼' : '▶' }}
          </button>
          <span v-else class="w-6"></span>

          <!-- Icon and Name -->
          <span class="text-xl">{{ getIcon(site.type) }}</span>
          <span class="font-medium text-gray-800 flex-1">{{ site.name }}</span>

          <!-- Action Buttons -->
          <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
            <button
              @click="emit('edit-resource', site.type, site.id)"
              class="p-1 hover:bg-gray-200 rounded"
              title="Settings"
            >
              ⚙️
            </button>
            <button
              @click="emit('manage-permissions', site.type, site.id, site.name)"
              class="p-1 hover:bg-gray-200 rounded"
              title="Manage Permissions"
            >
              🔑
            </button>
          </div>
        </div>

        <!-- Plan Level -->
        <div v-if="site.expanded && site.children" class="ml-8 space-y-2">
          <div v-for="plan in site.children" :key="plan.id" class="border-l-2 border-gray-200 pl-2">
            <div class="flex items-center gap-2 py-2 hover:bg-gray-50 rounded px-2 group">
              <!-- Expand/Collapse Button -->
              <button
                v-if="plan.children && plan.children.length > 0"
                @click="toggleNode(plan.id)"
                class="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-gray-800"
              >
                {{ plan.expanded ? '▼' : '▶' }}
              </button>
              <span v-else class="w-6"></span>

              <!-- Icon and Name -->
              <span class="text-xl">{{ getIcon(plan.type) }}</span>
              <span class="font-medium text-gray-700 flex-1">{{ plan.name }}</span>

              <!-- Action Buttons -->
              <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                <button
                  @click="emit('edit-resource', plan.type, plan.id)"
                  class="p-1 hover:bg-gray-200 rounded"
                  title="Settings"
                >
                  ⚙️
                </button>
                <button
                  @click="emit('manage-permissions', plan.type, plan.id, plan.name)"
                  class="p-1 hover:bg-gray-200 rounded"
                  title="Manage Permissions"
                >
                  🔑
                </button>
              </div>
            </div>

            <!-- Sensor/Broker Level -->
            <div v-if="plan.expanded && plan.children" class="ml-8 space-y-1">
              <div v-for="child in plan.children" :key="child.id" class="border-l-2 border-gray-200 pl-2">
                <!-- Sensor or Broker Node -->
                <div class="flex items-center gap-2 py-2 hover:bg-gray-50 rounded px-2 group">
                  <!-- Expand/Collapse Button (only for sensors with alarms) -->
                  <button
                    v-if="child.type === 'sensor' && child.children && child.children.length > 0"
                    @click="toggleNode(child.id)"
                    class="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-gray-800"
                  >
                    {{ child.expanded ? '▼' : '▶' }}
                  </button>
                  <span v-else class="w-6"></span>

                  <!-- Icon and Name -->
                  <span class="text-xl">{{ getIcon(child.type) }}</span>
                  <span class="text-gray-700 flex-1">
                    {{ child.name }}
                    <span v-if="child.type === 'broker' && child.protocol" class="text-xs text-gray-500 ml-2">
                      ({{ child.protocol }})
                    </span>
                  </span>

                  <!-- Action Buttons -->
                  <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                    <button
                      @click="emit('edit-resource', child.type, child.id)"
                      class="p-1 hover:bg-gray-200 rounded"
                      title="Settings"
                    >
                      ⚙️
                    </button>
                    <button
                      @click="emit('manage-permissions', child.type, child.id, child.name)"
                      class="p-1 hover:bg-gray-200 rounded"
                      title="Manage Permissions"
                    >
                      🔑
                    </button>
                  </div>
                </div>

                <!-- Alarm Level (only for sensors) -->
                <div v-if="child.type === 'sensor' && child.expanded && child.children" class="ml-8 space-y-1">
                  <div v-for="alarm in child.children" :key="alarm.id" class="border-l-2 border-gray-200 pl-2">
                    <div class="flex items-center gap-2 py-2 hover:bg-gray-50 rounded px-2 group">
                      <!-- Expand/Collapse Button (for alarms with alerts) -->
                      <button
                        v-if="alarm.children && alarm.children.length > 0"
                        @click="toggleNode(alarm.id)"
                        class="w-6 h-6 flex items-center justify-center text-gray-600 hover:text-gray-800"
                      >
                        {{ alarm.expanded ? '▼' : '▶' }}
                      </button>
                      <span v-else class="w-6"></span>

                      <!-- Icon and Name -->
                      <span class="text-xl">{{ getIcon(alarm.type) }}</span>
                      <span class="text-gray-700 flex-1">{{ alarm.name }}</span>

                      <!-- Action Buttons -->
                      <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                        <button
                          @click="emit('edit-resource', alarm.type, alarm.id)"
                          class="p-1 hover:bg-gray-200 rounded"
                          title="Settings"
                        >
                          ⚙️
                        </button>
                        <button
                          @click="emit('manage-permissions', alarm.type, alarm.id, alarm.name)"
                          class="p-1 hover:bg-gray-200 rounded"
                          title="Manage Permissions"
                        >
                          🔑
                        </button>
                      </div>
                    </div>

                    <!-- Alert Level -->
                    <div v-if="alarm.expanded && alarm.children" class="ml-8 space-y-1">
                      <div v-for="alert in alarm.children" :key="alert.id"
                           class="flex items-center gap-2 py-2 hover:bg-gray-50 rounded px-2 group">
                        <span class="w-6"></span>
                        <span class="text-xl">{{ getIcon(alert.type) }}</span>
                        <span class="text-gray-700 flex-1">
                          {{ alert.name }}
                          <span v-if="alert.severity"
                                :class="{
                                  'text-red-600 font-semibold': alert.severity === 'critical' || alert.severity === 'high',
                                  'text-orange-600': alert.severity === 'medium',
                                  'text-yellow-600': alert.severity === 'low'
                                }"
                                class="text-xs ml-2">
                            [{{ alert.severity }}]
                          </span>
                        </span>

                        <!-- Action Buttons -->
                        <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                          <button
                            @click="emit('edit-resource', alert.type, alert.id)"
                            class="p-1 hover:bg-gray-200 rounded"
                            title="Settings"
                          >
                            ⚙️
                          </button>
                          <button
                            @click="emit('manage-permissions', alert.type, alert.id, alert.name)"
                            class="p-1 hover:bg-gray-200 rounded"
                            title="Manage Permissions"
                          >
                            🔑
                          </button>
                        </div>
                      </div>

                      <!-- Empty state for alerts -->
                      <div v-if="alarm.children.length === 0" class="ml-6 text-gray-400 text-sm py-2">
                        (no alerts)
                      </div>
                    </div>
                  </div>

                  <!-- Empty state for alarms -->
                  <div v-if="child.children && child.children.length === 0" class="ml-6 text-gray-400 text-sm py-2">
                    (no alarms)
                  </div>
                </div>
              </div>

              <!-- Empty state for sensors/brokers -->
              <div v-if="plan.children.length === 0" class="ml-6 text-gray-400 text-sm py-2">
                (no sensors or brokers)
              </div>
            </div>
          </div>

          <!-- Empty state for plans -->
          <div v-if="site.children.length === 0" class="ml-6 text-gray-400 text-sm py-2">
            (no plans)
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
