// Dashboard API client
import apiClient from './client'
import type { Dashboard, CreateDashboardRequest } from '@/types'

// Dashboards
export const fetchDashboards = async (): Promise<Dashboard[]> => {
  const response = await apiClient.get<Dashboard[]>('/dashboards')
  return response.data
}

export const fetchDashboard = async (id: string, includePermissions = false): Promise<Dashboard> => {
  const response = await apiClient.get<Dashboard>(`/dashboards/${id}`, {
    params: { include_permissions: includePermissions }
  })
  return response.data
}

export const createDashboard = async (data: CreateDashboardRequest): Promise<Dashboard> => {
  const response = await apiClient.post<Dashboard>('/dashboards', {
    ...data,
    config: data.config || {}
  })
  return response.data
}

export const updateDashboard = async (id: string, data: CreateDashboardRequest): Promise<Dashboard> => {
  const response = await apiClient.put<Dashboard>(`/dashboards/${id}`, data)
  return response.data
}

export const deleteDashboard = async (id: string): Promise<void> => {
  await apiClient.delete(`/dashboards/${id}`)
}
