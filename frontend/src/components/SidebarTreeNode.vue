<template>
  <div class="sidebar-tree-node">
    <!-- Node Content -->
    <div
      class="node-content"
      :class="{
        'active': isActive,
        'has-children': hasChildren
      }"
      :style="{ paddingLeft: `${depth * 16 + 8}px` }"
      @click="handleClick"
    >
      <!-- Expand/Collapse Chevron -->
      <button
        v-if="hasChildren"
        class="chevron-btn"
        @click.stop="toggleExpand"
      >
        <svg
          class="chevron-icon"
          :class="{ 'expanded': isExpanded }"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fill-rule="evenodd"
            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
            clip-rule="evenodd"
          />
        </svg>
      </button>
      <span v-else class="chevron-spacer"></span>

      <!-- Icon -->
      <span class="node-icon">{{ icon }}</span>

      <!-- Name -->
      <span class="node-name">{{ node.name }}</span>
    </div>

    <!-- Children (recursive) -->
    <transition name="expand">
      <div v-if="isExpanded && hasChildren" class="node-children">
        <SidebarTreeNode
          v-for="child in node.children"
          :key="child.id"
          :node="child"
          :depth="depth + 1"
          :expanded-nodes="expandedNodes"
          :active-node-id="activeNodeId"
          @toggle="$emit('toggle', $event)"
          @select="$emit('select', $event)"
        />
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

interface TreeNode {
  id: string
  name: string
  type: 'site' | 'plan' | 'sensor' | 'alarm' | 'broker'
  children?: TreeNode[]
}

interface Props {
  node: TreeNode
  depth: number
  expandedNodes: Set<string>
  activeNodeId?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  toggle: [nodeId: string]
  select: [node: TreeNode]
}>()

const router = useRouter()

const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})

const isExpanded = computed(() => {
  return props.expandedNodes.has(props.node.id)
})

const isActive = computed(() => {
  return props.activeNodeId === props.node.id
})

const icon = computed(() => {
  switch (props.node.type) {
    case 'site': return '🏭'
    case 'plan': return '📋'
    case 'sensor': return '📡'
    case 'alarm': return '🔔'
    case 'broker': return '📶'
    default: return '📄'
  }
})

function toggleExpand() {
  emit('toggle', props.node.id)
}

function handleClick() {
  emit('select', props.node)

  // Navigate to resource detail page
  const routeMap: Record<string, string> = {
    site: 'SiteDetail',
    plan: 'PlanDetail',
    sensor: 'SensorDetail',
    alarm: 'AlarmDetail',
    broker: 'BrokerDetail'
  }

  const routeName = routeMap[props.node.type]
  if (routeName) {
    router.push({ name: routeName, params: { id: props.node.id } })
  }
}
</script>

<style scoped>
.sidebar-tree-node {
  user-select: none;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  padding-right: 8px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
  position: relative;
}

.node-content:hover {
  background-color: rgba(59, 130, 246, 0.1);
}

.node-content.active {
  background-color: rgba(59, 130, 246, 0.15);
  font-weight: 600;
}

.node-content.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: #3b82f6;
  border-radius: 0 3px 3px 0;
}

.chevron-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  transition: transform 0.2s ease;
  border-radius: 4px;
}

.chevron-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.chevron-spacer {
  width: 20px;
  height: 20px;
}

.chevron-icon {
  width: 16px;
  height: 16px;
  transition: transform 0.2s ease;
  transform: rotate(0deg);
}

.chevron-icon.expanded {
  transform: rotate(90deg);
}

.node-icon {
  font-size: 18px;
  line-height: 1;
  flex-shrink: 0;
}

.node-name {
  flex: 1;
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-content.active .node-name {
  color: #1f2937;
}

.node-children {
  overflow: hidden;
}

/* Expand/Collapse Animation */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px;
  opacity: 1;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
