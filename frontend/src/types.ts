// User and Authentication Types
export interface User {
  id: number
  username: string
  email?: string
  is_active: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

// Resource Types
export type ResourceType = 'site' | 'area' | 'sensor'

export interface Resource {
  id: number
  name: string
  type: ResourceType
  parent_id: number | null
  path: string
  created_at: string
  updated_at: string
  children?: Resource[]
}

export interface CreateResourceRequest {
  name: string
  type: ResourceType
  parent_id: number | null
}

// Permission Types
export type PermissionLevel = 'none' | 'read' | 'write' | 'manage'

export interface Permission {
  id: number
  resource_id: number
  user_id: number | null
  group_id: number | null
  permission: PermissionLevel
  inherit: boolean
  granted_by: number
  granted_at: string
}

export interface GrantPermissionRequest {
  resource_id: number
  user_id?: number
  group_id?: number
  permission: PermissionLevel
  inherit: boolean
}

export interface PermissionCheck {
  resource_id: number
  user_id: number
  effective_permission: PermissionLevel
  direct_permissions: Permission[]
  inherited_permissions: Permission[]
  group_permissions: Permission[]
}

export interface MyPermission {
  id: string
  grantee_type: string
  grantee_id: string
  grantee_name: string
  resource_type: string
  resource_id: string
  resource_name: string
  permission: string
  effect: string
  inherit: boolean
  granted_by: string | null
  granted_at: string
  via?: string
}

export interface MyPermissions {
  direct: Array<{
    resource: Resource
    permission: Permission
  }>
  via_groups: Array<{
    resource: Resource
    permission: Permission
    group_name: string
  }>
}

// Group Types
export interface Group {
  id: number
  name: string
  description?: string
  created_at: string
  updated_at: string
}

export interface CreateGroupRequest {
  name: string
  description?: string
}

export interface GroupMembership {
  id: number
  user_id: number
  group_id: number
  added_by: number
  added_at: string
}

// API Error Types
export interface APIError {
  detail: string
}
