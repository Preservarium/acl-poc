<script setup lang="ts">
import { ref } from 'vue'

interface Permission {
  permission: string
  effect: string
  fields?: string[] | null
  source: string
  is_inherited: boolean
  depth: number
}

interface TreeNode {
  id: string
  name: string
  type: string
  permissions: Permission[]
  denies: Permission[]
  children: TreeNode[]
}

const props = defineProps<{
  node: TreeNode
  depth?: number
}>()

const isExpanded = ref(true)

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const getIcon = (type: string): string => {
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

const getPermissionColor = (permission: string): string => {
  switch (permission) {
    case 'manage': return 'bg-purple-100 text-purple-800'
    case 'create': return 'bg-blue-100 text-blue-800'
    case 'delete': return 'bg-red-100 text-red-800'
    case 'write': return 'bg-green-100 text-green-800'
    case 'read': return 'bg-gray-100 text-gray-800'
    default: return 'bg-gray-100 text-gray-700'
  }
}

const formatFields = (fields: string[] | null | undefined): string => {
  if (!fields || fields.length === 0) return ''
  return `(${fields.join(', ')})`
}

const currentDepth = props.depth ?? 0
</script>

<template>
  <div class="tree-node">
    <!-- Node Header -->
    <div
      class="node-header flex items-center py-2 px-3 hover:bg-gray-50 rounded cursor-pointer"
      :style="{ paddingLeft: `${currentDepth * 24 + 12}px` }"
      @click="toggleExpand"
    >
      <!-- Expand/Collapse Icon -->
      <span v-if="node.children && node.children.length > 0" class="mr-2 text-gray-500 transition-transform" :class="{ 'rotate-90': isExpanded }">
        ▶
      </span>
      <span v-else class="mr-2 w-4"></span>

      <!-- Resource Icon and Name -->
      <span class="icon mr-2 text-xl">{{ getIcon(node.type) }}</span>
      <span class="font-medium text-gray-900">{{ node.name }}</span>
      <span class="text-xs text-gray-500 ml-2">({{ node.type }})</span>

      <!-- Permission Badges -->
      <div class="ml-4 flex flex-wrap gap-2">
        <!-- Allow Permissions -->
        <div v-for="perm in node.permissions" :key="`allow-${perm.permission}-${perm.source}`" class="flex items-center gap-1">
          <span :class="getPermissionColor(perm.permission)" class="text-xs px-2 py-1 rounded font-medium">
            {{ perm.permission }}
            <span v-if="perm.fields && perm.fields.length > 0" class="text-xs opacity-75">
              {{ formatFields(perm.fields) }}
            </span>
          </span>
          <span class="text-xs text-gray-500">
            {{ perm.is_inherited ? '← inherited' : '' }} {{ perm.source }}
          </span>
        </div>

        <!-- Deny Permissions -->
        <div v-for="deny in node.denies" :key="`deny-${deny.permission}-${deny.source}`" class="flex items-center gap-1">
          <span class="bg-red-200 text-red-900 text-xs px-2 py-1 rounded font-bold">
            🚫 DENY {{ deny.permission }}
          </span>
          <span class="text-xs text-red-600">
            {{ deny.is_inherited ? '← inherited' : '' }} {{ deny.source }}
          </span>
        </div>
      </div>
    </div>

    <!-- Children -->
    <div v-if="isExpanded && node.children && node.children.length > 0" class="children">
      <InheritanceNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="currentDepth + 1"
      />
    </div>
  </div>
</template>

<style scoped>
.tree-node {
  font-size: 0.875rem;
}

.node-header:hover {
  background-color: #f9fafb;
}

.rotate-90 {
  transform: rotate(90deg);
}
</style>
