// Permission API client
import apiClient from './client'
import type {
  Permission,
  MyPermission,
  GrantPermissionRequest,
  PermissionCheck,
  PermissionCheckResult,
  PermissionWithGrantee,
  PlanPermissionsResponse,
  PermissionMatrixResponse,
  ExpiringPermission
} from '@/types'

// Fetch all permissions (admin only)
export const fetchPermissions = async (): Promise<Permission[]> => {
  const response = await apiClient.get<Permission[]>('/permissions/all')
  return response.data
}

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

// Fetch permissions for a site with grantee details
export const fetchSitePermissions = async (siteId: string): Promise<PermissionWithGrantee[]> => {
  const response = await apiClient.get<PermissionWithGrantee[]>(`/sites/${siteId}/permissions`)
  return response.data
}

// Fetch permissions for a plan with inherited/direct/effective sections
export const fetchPlanPermissions = async (
  planId: string,
  includeInherited: boolean = true,
  includeEffective: boolean = true
): Promise<PlanPermissionsResponse> => {
  const response = await apiClient.get<PlanPermissionsResponse>(
    `/plans/${planId}/permissions`,
    {
      params: {
        include_inherited: includeInherited,
        include_effective: includeEffective
      }
    }
  )
  return response.data
}

// Fetch resource hierarchy (for displaying parent resources)
export const fetchResourceHierarchy = async (
  resourceType: string,
  resourceId: string
): Promise<Array<{ type: string; id: string; name: string }>> => {
  try {
    const response = await apiClient.get<Array<{ type: string; id: string; name: string }>>(
      `/resources/${resourceType}/${resourceId}/hierarchy`
    )
    return response.data
  } catch (err) {
    // Fallback: return empty array if endpoint doesn't exist
    console.warn('Resource hierarchy endpoint not available:', err)
    return []
  }
}

// Check for existing permissions for a grantee on a resource
export const checkExistingPermissions = async (
  granteeType: string,
  granteeId: string,
  resourceType: string,
  resourceId: string
): Promise<Array<{
  permission: string
  fields?: string[]
  source: string
  isInherited?: boolean
  isDirect?: boolean
}>> => {
  try {
    const response = await apiClient.get(
      `/permissions/check-existing`,
      {
        params: {
          grantee_type: granteeType,
          grantee_id: granteeId,
          resource_type: resourceType,
          resource_id: resourceId
        }
      }
    )
    return response.data
  } catch (err) {
    // If endpoint doesn't exist, return empty array
    console.warn('Existing permissions check not available:', err)
    return []
  }
}

// Fetch permission matrix for a resource
export const fetchPermissionMatrix = async (
  resourceType: string,
  resourceId: string
): Promise<PermissionMatrixResponse> => {
  const response = await apiClient.get<PermissionMatrixResponse>(
    '/permissions/matrix',
    {
      params: {
        resource_type: resourceType,
        resource_id: resourceId
      }
    }
  )
  return response.data
}

// Fetch expiring permissions (admin only)
export const fetchExpiringPermissions = async (
  daysAhead: number = 7
): Promise<ExpiringPermission[]> => {
  const response = await apiClient.get<ExpiringPermission[]>(
    '/permissions/expiring',
    {
      params: {
        days_ahead: daysAhead
      }
    }
  )
  return response.data
}
