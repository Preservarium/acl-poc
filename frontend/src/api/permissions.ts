// Permission API client
import apiClient from './client'
import type {
  Permission,
  MyPermission,
  GrantPermissionRequest,
  PermissionCheck,
  PermissionCheckResult
} from '@/types'

// Fetch user's permissions
export const fetchMyPermissions = async (): Promise<{
  direct: MyPermission[]
  via_groups: MyPermission[]
}> => {
  const response = await apiClient.get<Permission[]>('/permissions')

  // Transform the flat array into direct and via_groups
  const direct: MyPermission[] = []
  const via_groups: MyPermission[] = []

  response.data.forEach((perm) => {
    const myPerm: MyPermission = {
      resource_type: perm.resource_type,
      resource_id: perm.resource_id,
      resource_name: perm.resource_name || `${perm.resource_type}:${perm.resource_id}`,
      permission: perm.permission,
      inherit: perm.inherit,
      via: perm.grantee_type === 'user' ? 'me' : (perm.grantee_name || perm.grantee_id),
      via_type: perm.grantee_type === 'user' ? 'direct' : 'group'
    }

    if (perm.grantee_type === 'user') {
      direct.push(myPerm)
    } else {
      via_groups.push(myPerm)
    }
  })

  return { direct, via_groups }
}

// Fetch permissions for a specific resource
export const fetchResourcePermissions = async (
  resourceType: string,
  resourceId: string
): Promise<Permission[]> => {
  const response = await apiClient.get<Permission[]>(
    `/permissions/resource/${resourceType}/${resourceId}`
  )
  return response.data
}

// Grant a new permission
export const grantPermission = async (data: GrantPermissionRequest): Promise<Permission> => {
  const response = await apiClient.post<Permission>('/permissions', {
    ...data,
    effect: data.effect || 'allow',
    inherit: data.inherit !== undefined ? data.inherit : true
  })
  return response.data
}

// Revoke a permission
export const revokePermission = async (permissionId: string): Promise<void> => {
  await apiClient.delete(`/permissions/${permissionId}`)
}

// Check multiple permissions at once
export const checkPermissions = async (
  checks: PermissionCheck[]
): Promise<{ results: PermissionCheckResult[] }> => {
  const response = await apiClient.post<{ results: PermissionCheckResult[] }>(
    '/permissions/check',
    { checks }
  )
  return response.data
}

// Check single permission (convenience method)
export const checkPermission = async (
  resourceType: string,
  resourceId: string,
  permission: string
): Promise<boolean> => {
  const result = await checkPermissions([
    { resource_type: resourceType as any, resource_id: resourceId, permission: permission as any }
  ])
  return result.results[0]?.allowed || false
}
