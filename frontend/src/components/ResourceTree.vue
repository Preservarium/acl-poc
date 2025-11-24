<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { fetchSites, fetchPlans, fetchSensors } from '@/api/resources'
import type { Site, Plan, Sensor } from '@/types'

interface TreeNode {
  id: string
  name: string
  type: 'site' | 'plan' | 'sensor'
  expanded: boolean
  children?: TreeNode[]
  parent_id?: string
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
const loading = ref(false)
const error = ref<string | null>(null)

// Track expanded state
const expandedNodes = ref<Set<string>>(new Set())

const loadData = async () => {
  loading.value = true
  error.value = null
  try {
    const [sitesData, plansData, sensorsData] = await Promise.all([
      fetchSites(),
      fetchPlans(),
      fetchSensors()
    ])
    sites.value = sitesData
    plans.value = plansData
    sensors.value = sensorsData
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
        return {
          id: plan.id,
          name: plan.name,
          type: 'plan' as const,
          expanded: isExpanded(plan.id),
          parent_id: site.id,
          children: planSensors.map(sensor => ({
            id: sensor.id,
            name: sensor.name,
            type: 'sensor' as const,
            expanded: false,
            parent_id: plan.id
          }))
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

            <!-- Sensor Level -->
            <div v-if="plan.expanded && plan.children" class="ml-8 space-y-1">
              <div v-for="sensor in plan.children" :key="sensor.id"
                   class="flex items-center gap-2 py-2 hover:bg-gray-50 rounded px-2 group">
                <span class="w-6"></span>
                <span class="text-xl">{{ getIcon(sensor.type) }}</span>
                <span class="text-gray-700 flex-1">{{ sensor.name }}</span>

                <!-- Action Buttons -->
                <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                  <button
                    @click="emit('edit-resource', sensor.type, sensor.id)"
                    class="p-1 hover:bg-gray-200 rounded"
                    title="Settings"
                  >
                    ⚙️
                  </button>
                  <button
                    @click="emit('manage-permissions', sensor.type, sensor.id, sensor.name)"
                    class="p-1 hover:bg-gray-200 rounded"
                    title="Manage Permissions"
                  >
                    🔑
                  </button>
                </div>
              </div>

              <!-- Empty state for sensors -->
              <div v-if="plan.children.length === 0" class="ml-6 text-gray-400 text-sm py-2">
                (no sensors)
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
