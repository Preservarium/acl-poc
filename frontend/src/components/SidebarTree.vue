<template>
  <div class="sidebar-tree">
    <!-- Header -->
    <div class="tree-header">
      <div class="header-content">
        <span class="header-icon">🏭</span>
        <span class="header-title">Sites</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="tree-loading">
      <div class="loading-spinner"></div>
      <span class="loading-text">Loading...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="tree-error">
      <span class="error-icon">⚠️</span>
      <span class="error-text">{{ error }}</span>
      <button @click="loadData" class="retry-btn">Retry</button>
    </div>

    <!-- Tree Content -->
    <div v-else class="tree-content">
      <!-- Empty State -->
      <div v-if="treeData.length === 0" class="tree-empty">
        <span class="empty-icon">📭</span>
        <span class="empty-text">No sites yet</span>
      </div>

      <!-- Tree Nodes -->
      <div v-else class="tree-nodes">
        <SidebarTreeNode
          v-for="site in treeData"
          :key="site.id"
          :node="site"
          :depth="0"
          :expanded-nodes="expandedNodes"
          :active-node-id="activeNodeId"
          @toggle="toggleNode"
          @select="handleSelect"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { fetchSites, fetchPlans, fetchSensors, fetchAlarms, fetchBrokers } from '@/api/resources'
import type { Site, Plan, Sensor, Alarm, Broker } from '@/types'
import SidebarTreeNode from './SidebarTreeNode.vue'

interface TreeNode {
  id: string
  name: string
  type: 'site' | 'plan' | 'sensor' | 'alarm' | 'broker'
  children?: TreeNode[]
}

const route = useRoute()

const sites = ref<Site[]>([])
const plans = ref<Plan[]>([])
const sensors = ref<Sensor[]>([])
const alarms = ref<Alarm[]>([])
const brokers = ref<Broker[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// Track expanded and selected nodes
const expandedNodes = ref<Set<string>>(new Set())
const selectedNode = ref<TreeNode | null>(null)

// Compute active node from route
const activeNodeId = computed(() => {
  const routeName = route.name as string
  const id = route.params.id as string

  if (!id) return undefined

  // Map route names to resource types
  const routeToType: Record<string, string> = {
    'SiteDetail': 'site',
    'PlanDetail': 'plan',
    'SensorDetail': 'sensor',
    'AlarmDetail': 'alarm',
    'BrokerDetail': 'broker'
  }

  if (routeToType[routeName]) {
    return id
  }

  return undefined
})

// Load all resource data
const loadData = async () => {
  loading.value = true
  error.value = null

  try {
    const [sitesData, plansData, sensorsData, alarmsData, brokersData] = await Promise.all([
      fetchSites(),
      fetchPlans(),
      fetchSensors(),
      fetchAlarms(),
      fetchBrokers()
    ])

    sites.value = sitesData
    plans.value = plansData
    sensors.value = sensorsData
    alarms.value = alarmsData
    brokers.value = brokersData

    // Auto-expand path to active node
    if (activeNodeId.value) {
      expandPathToNode(activeNodeId.value)
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load resources'
  } finally {
    loading.value = false
  }
}

// Build hierarchical tree structure
const treeData = computed<TreeNode[]>(() => {
  return sites.value.map(site => {
    const sitePlans = plans.value.filter(plan => plan.site_id === site.id)

    return {
      id: site.id,
      name: site.name,
      type: 'site' as const,
      children: sitePlans.map(plan => {
        const planSensors = sensors.value.filter(sensor => sensor.plan_id === plan.id)
        const planBrokers = brokers.value.filter(broker => broker.plan_id === plan.id)

        const planChildren: TreeNode[] = []

        // Add sensors with their alarms
        planSensors.forEach(sensor => {
          const sensorAlarms = alarms.value.filter(alarm => alarm.sensor_id === sensor.id)

          planChildren.push({
            id: sensor.id,
            name: sensor.name,
            type: 'sensor' as const,
            children: sensorAlarms.map(alarm => ({
              id: alarm.id,
              name: alarm.name,
              type: 'alarm' as const
            }))
          })
        })

        // Add brokers
        planBrokers.forEach(broker => {
          planChildren.push({
            id: broker.id,
            name: broker.name,
            type: 'broker' as const
          })
        })

        return {
          id: plan.id,
          name: plan.name,
          type: 'plan' as const,
          children: planChildren
        }
      })
    }
  })
})

// Toggle node expansion
function toggleNode(nodeId: string) {
  if (expandedNodes.value.has(nodeId)) {
    expandedNodes.value.delete(nodeId)
  } else {
    expandedNodes.value.add(nodeId)
  }
}

// Handle node selection
function handleSelect(node: TreeNode) {
  selectedNode.value = node
}

// Expand path to a specific node (for deep linking)
function expandPathToNode(nodeId: string) {
  // Find the node and its parents
  const pathIds: string[] = []

  function findPath(nodes: TreeNode[], targetId: string, currentPath: string[]): boolean {
    for (const node of nodes) {
      const newPath = [...currentPath, node.id]

      if (node.id === targetId) {
        pathIds.push(...newPath.slice(0, -1)) // Add all parent IDs
        return true
      }

      if (node.children && findPath(node.children, targetId, newPath)) {
        return true
      }
    }
    return false
  }

  findPath(treeData.value, nodeId, [])

  // Expand all parent nodes
  pathIds.forEach(id => {
    expandedNodes.value.add(id)
  })
}

// Expose refresh method for parent components
defineExpose({
  refresh: loadData
})

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.sidebar-tree {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f9fafb;
  border-right: 1px solid #e5e7eb;
}

.tree-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  background-color: white;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 20px;
  line-height: 1;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.tree-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 14px;
  color: #6b7280;
}

.tree-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  text-align: center;
}

.error-icon {
  font-size: 32px;
}

.error-text {
  font-size: 14px;
  color: #dc2626;
}

.retry-btn {
  margin-top: 8px;
  padding: 6px 16px;
  font-size: 14px;
  color: #3b82f6;
  background: none;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.retry-btn:hover {
  background-color: #eff6ff;
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tree-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px 16px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.empty-text {
  font-size: 14px;
  color: #9ca3af;
}

.tree-nodes {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Custom scrollbar */
.tree-content::-webkit-scrollbar {
  width: 6px;
}

.tree-content::-webkit-scrollbar-track {
  background: transparent;
}

.tree-content::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

.tree-content::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
