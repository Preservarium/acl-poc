// Type definitions for ACL PoC

export interface User {
  id: string
  username: string
  email?: string
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
  _permissions?: PermissionMetadata
}

export interface Plan {
  id: string
  name: string
  site_id: string
  created_by: string
  created_at: string
  _permissions?: PermissionMetadata
}

export interface Sensor {
  id: string
  name: string
  plan_id: string
  created_by: string
  created_at: string
  _permissions?: PermissionMetadata
}

export interface Alarm {
  id: string
  name: string
  sensor_id: string
  created_by: string
  created_at: string
  _permissions?: PermissionMetadata
}

export interface Alert {
  id: string
  message: string
  severity: string
  alarm_id: string
  created_by: string
  created_at: string
  _permissions?: PermissionMetadata
}

export interface Broker {
  id: string
  name: string
  protocol: string
  plan_id: string
  created_by: string
  created_at: string
  _permissions?: PermissionMetadata
}

export interface Dashboard {
  id: string
  name: string
  config: Record<string, any>
  created_by: string
  created_at: string
  _permissions?: PermissionMetadata
}

export type ResourceType = 'site' | 'plan' | 'sensor' | 'alarm' | 'alert' | 'broker' | 'dashboard' | 'group' | 'user'
export type GranteeType = 'user' | 'group'
export type PermissionType = 'read' | 'write' | 'delete' | 'create' | 'manage' | 'member'
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
  expires_at?: string
  fields?: string[]
}

export interface PermissionWithGrantee {
  id: string
  grantee_type: GranteeType
  grantee_id: string
  grantee_name: string
  permission: PermissionType
  effect: EffectType
  inherit: boolean
  fields?: string[]
  expires_at?: string
  granted_at: string
  granted_by_name?: string
  source?: string  // For inherited permissions, shows the parent resource
  members?: string[]
  member_count?: number
}

export interface EffectivePermission {
  user_id: string
  username: string
  permissions: string[]  // e.g., ['read', 'write']
  fields?: string[]  // Combined fields, null/undefined means all
  sources: string[]  // e.g., ['Factory 1 Admins', 'direct']
}

export interface ParentInfo {
  type: string  // 'site', 'plan', etc.
  id: string
  name: string
}

export interface PlanPermissionsResponse {
  parent: ParentInfo
  inherited: PermissionWithGrantee[]
  direct: PermissionWithGrantee[]
  effective: EffectivePermission[]
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

export interface PermissionMetadata {
  can_read: boolean
  can_write: boolean
  can_delete: boolean
  can_create: boolean
  can_manage: boolean
  writable_fields?: string[]
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

export interface CreateAlarmRequest {
  name: string
  sensor_id: string
}

export interface CreateAlertRequest {
  message: string
  severity: string
  alarm_id: string
}

export interface CreateBrokerRequest {
  name: string
  protocol: string
  plan_id: string
}

export interface CreateDashboardRequest {
  name: string
  config?: Record<string, any>
}

export interface GrantPermissionRequest {
  grantee_type: GranteeType
  grantee_id: string
  resource_type: ResourceType
  resource_id: string
  permission: PermissionType
  effect?: EffectType
  inherit?: boolean
  expires_at?: string
  fields?: string[]
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

export interface PermissionSource {
  permission: PermissionType
  allowed: boolean
  via: string
  via_type: 'direct' | 'group'
}

export interface PermissionDeniedDetail {
  detail: string
  required_permission: PermissionType
  resource_type: ResourceType
  resource_id: string
  resource_name?: string
  user_permissions: PermissionSource[]
}

export interface MatrixGrantee {
  grantee_id: string
  grantee_name: string
  grantee_type: GranteeType
}

export interface MatrixPermissionInfo {
  allowed: boolean
  inherited: boolean
  has_field_restrictions: boolean
  fields?: string[]
  source?: string
}

export interface MatrixRow {
  grantee: MatrixGrantee
  permissions: {
    read: MatrixPermissionInfo
    write: MatrixPermissionInfo
    delete: MatrixPermissionInfo
    create: MatrixPermissionInfo
    manage: MatrixPermissionInfo
  }
}

export interface PermissionMatrixResponse {
  resource_type: string
  resource_id: string
  resource_name: string
  grantees: MatrixRow[]
}

export interface EffectivePermissionsResponse {
  user: {
    id: string
    username: string
  }
  groups: Array<{
    id: string
    name: string
  }>
  sites_administered: ResourceWithSource[]
  sites_write: ResourceWithSource[]
  sites_read: ResourceWithSource[]
  direct_permissions: DirectPermission[]
}

export interface ResourceWithSource {
  resource_id: string
  resource_name: string
  resource_type: ResourceType
  permission: PermissionType
  source: string
}

export interface DirectPermission {
  resource_id: string
  resource_name: string
  resource_type: ResourceType
  permission: PermissionType
  source: string
}

export interface ExpiringPermission {
  id: string
  grantee_type: GranteeType
  grantee_id: string
  grantee_name?: string
  resource_type: ResourceType
  resource_id: string
  resource_name?: string
  permission: PermissionType
  effect: EffectType
  expires_at: string
  granted_at: string
  granted_by?: string
  days_until_expiry: number
}
