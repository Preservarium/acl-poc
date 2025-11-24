import { defineStore } from 'pinia'
import { ref } from 'vue'
import { permissionsAPI } from '@/api/permissions'
import type {
  Permission,
  GrantPermissionRequest,
  MyPermissions,
  PermissionLevel
} from '@/types'

export const usePermissionsStore = defineStore('permissions', () => {
  // State
  const resourcePermissions = ref<Map<number, Permission[]>>(new Map())
  const myPermissions = ref<MyPermissions | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function grantPermission(data: GrantPermissionRequest): Promise<Permission> {
    loading.value = true
    error.value = null

    try {
      const permission = await permissionsAPI.grantPermission(data)

      // Refresh the resource permissions
      await fetchResourcePermissions(data.resource_id)

      return permission
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to grant permission'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function revokePermission(permissionId: number, resourceId: number): Promise<void> {
    loading.value = true
    error.value = null

    try {
      await permissionsAPI.revokePermission(permissionId)

      // Refresh the resource permissions
      await fetchResourcePermissions(resourceId)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to revoke permission'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchResourcePermissions(resourceId: number): Promise<Permission[]> {
    loading.value = true
    error.value = null

    try {
      const permissions = await permissionsAPI.getResourcePermissions(resourceId)
      resourcePermissions.value.set(resourceId, permissions)
      return permissions
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch permissions'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchMyPermissions(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      myPermissions.value = await permissionsAPI.getMyPermissions()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch my permissions'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function checkPermission(
    resourceId: number,
    requiredLevel: PermissionLevel
  ): Promise<boolean> {
    try {
      return await permissionsAPI.hasPermission(resourceId, requiredLevel)
    } catch {
      return false
    }
  }

  function getResourcePermissions(resourceId: number): Permission[] {
    return resourcePermissions.value.get(resourceId) || []
  }

  function clearCache(): void {
    resourcePermissions.value.clear()
    myPermissions.value = null
  }

  return {
    // State
    resourcePermissions,
    myPermissions,
    loading,
    error,
    // Actions
    grantPermission,
    revokePermission,
    fetchResourcePermissions,
    fetchMyPermissions,
    checkPermission,
    getResourcePermissions,
    clearCache
  }
})
