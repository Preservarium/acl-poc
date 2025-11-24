import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { resourcesAPI } from '@/api/resources'
import type { Resource, CreateResourceRequest } from '@/types'

export const useResourcesStore = defineStore('resources', () => {
  // State
  const resources = ref<Resource[]>([])
  const selectedResource = ref<Resource | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const resourceTree = computed(() => buildTree(resources.value))
  const rootResources = computed(() => resources.value.filter((r) => r.parent_id === null))

  // Actions
  async function fetchResources(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      resources.value = await resourcesAPI.getResources()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch resources'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchResourceTree(resourceId?: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      resources.value = await resourcesAPI.getResourceTree(resourceId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch resource tree'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createResource(data: CreateResourceRequest): Promise<Resource> {
    loading.value = true
    error.value = null

    try {
      const resource = await resourcesAPI.createResource(data)

      // Refresh resources
      await fetchResources()

      return resource
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create resource'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateResource(
    id: number,
    data: Partial<CreateResourceRequest>
  ): Promise<Resource> {
    loading.value = true
    error.value = null

    try {
      const resource = await resourcesAPI.updateResource(id, data)

      // Refresh resources
      await fetchResources()

      return resource
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update resource'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteResource(id: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      await resourcesAPI.deleteResource(id)

      // Refresh resources
      await fetchResources()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to delete resource'
      throw err
    } finally {
      loading.value = false
    }
  }

  function selectResource(resource: Resource | null): void {
    selectedResource.value = resource
  }

  function findResourceById(id: number): Resource | undefined {
    return resources.value.find((r) => r.id === id)
  }

  // Helper function to build tree structure
  function buildTree(items: Resource[]): Resource[] {
    const map = new Map<number, Resource>()
    const roots: Resource[] = []

    // Create a map of all items
    items.forEach((item) => {
      map.set(item.id, { ...item, children: [] })
    })

    // Build the tree
    map.forEach((item) => {
      if (item.parent_id === null) {
        roots.push(item)
      } else {
        const parent = map.get(item.parent_id)
        if (parent) {
          if (!parent.children) {
            parent.children = []
          }
          parent.children.push(item)
        }
      }
    })

    return roots
  }

  return {
    // State
    resources,
    selectedResource,
    loading,
    error,
    // Getters
    resourceTree,
    rootResources,
    // Actions
    fetchResources,
    fetchResourceTree,
    createResource,
    updateResource,
    deleteResource,
    selectResource,
    findResourceById
  }
})
