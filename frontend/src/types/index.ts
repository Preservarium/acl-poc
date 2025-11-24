// Type definitions for ACL PoC

export interface User {
  id: string
  username: string
  is_admin: boolean
  created_at: string
}

export interface Group {
  id: string
  name: string
  created_at: string
}

export interface Site {
  id: string
  name: string
  created_by: string
  created_at: string
}

export interface Plan {
  id: string
  name: string
  site_id: string
  created_by: string
  created_at: string
}

export interface Sensor {
  id: string
  name: string
  plan_id: string
  created_by: string
  created_at: string
}

export type ResourceType = 'site' | 'plan' | 'sensor'
export type GranteeType = 'user' | 'group'
export type PermissionType = 'read' | 'write' | 'delete' | 'create' | 'manage'
export type EffectType = 'allow' | 'deny'

export interface Permission {
  id: string
  grantee_type: GranteeType
  grantee_id: string
  grantee_name?: string
  resource_type: ResourceType
  resource_id: string
  resource_name?: string
  permission: PermissionType
  effect: EffectType
  inherit: boolean
  granted_by: string
  granted_at: string
}

export interface PermissionCheck {
  resource_type: ResourceType
  resource_id: string
  permission: PermissionType
}

export interface PermissionCheckResult {
  resource_type: ResourceType
  resource_id: string
  permission: PermissionType
  allowed: boolean
}

export interface MyPermission {
  resource_type: ResourceType
  resource_id: string
  resource_name: string
  permission: PermissionType
  inherit: boolean
  via: string // 'me' for direct, group name for inherited
  via_type: 'direct' | 'group'
}

export interface CreateSiteRequest {
  name: string
}

export interface CreatePlanRequest {
  name: string
  site_id: string
}

export interface CreateSensorRequest {
  name: string
  plan_id: string
}

export interface GrantPermissionRequest {
  grantee_type: GranteeType
  grantee_id: string
  resource_type: ResourceType
  resource_id: string
  permission: PermissionType
  effect?: EffectType
  inherit?: boolean
}

export interface ApiError {
  detail: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}
