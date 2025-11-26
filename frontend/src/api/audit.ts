// Audit logs API client
import apiClient from './client'

export interface AuditLog {
  id: string
  timestamp: string
  action: 'permission_granted' | 'permission_revoked' | 'permission_denied' | 'permission_expired'
  actor_id?: string
  actor_name?: string
  target_user_id?: string
  target_user_name?: string
  target_group_id?: string
  target_group_name?: string
  resource_type?: string
  resource_id?: string
  resource_name?: string
  permission?: string
  details?: Record<string, any>
}

export interface AuditLogFilters {
  action?: string
  user_id?: string
  date_from?: string
  date_to?: string
  days?: number
  page?: number
  page_size?: number
}

/**
 * Fetch audit logs with optional filters
 */
export async function fetchAuditLogs(filters?: AuditLogFilters): Promise<AuditLog[]> {
  const params = new URLSearchParams()

  if (filters?.action) params.append('action', filters.action)
  if (filters?.user_id) params.append('user_id', filters.user_id)
  if (filters?.date_from) params.append('date_from', filters.date_from)
  if (filters?.date_to) params.append('date_to', filters.date_to)
  if (filters?.days !== undefined) params.append('days', filters.days.toString())
  if (filters?.page) params.append('page', filters.page.toString())
  if (filters?.page_size) params.append('page_size', filters.page_size.toString())

  const response = await apiClient.get<AuditLog[]>(`/audit-logs?${params.toString()}`)
  return response.data
}

/**
 * Fetch a single audit log by ID
 */
export async function fetchAuditLog(id: string): Promise<AuditLog> {
  const response = await apiClient.get<AuditLog>(`/audit-logs/${id}`)
  return response.data
}
