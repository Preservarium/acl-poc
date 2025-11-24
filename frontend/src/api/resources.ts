// Resource API client for sites, plans, and sensors
import apiClient from './client'
import type {
  Site,
  Plan,
  Sensor,
  CreateSiteRequest,
  CreatePlanRequest,
  CreateSensorRequest
} from '@/types'

// Sites
export const fetchSites = async (): Promise<Site[]> => {
  const response = await apiClient.get<Site[]>('/sites')
  return response.data
}

export const fetchSite = async (id: string): Promise<Site> => {
  const response = await apiClient.get<Site>(`/sites/${id}`)
  return response.data
}

export const createSite = async (data: CreateSiteRequest): Promise<Site> => {
  const response = await apiClient.post<Site>('/sites', data)
  return response.data
}

export const updateSite = async (id: string, data: CreateSiteRequest): Promise<Site> => {
  const response = await apiClient.put<Site>(`/sites/${id}`, data)
  return response.data
}

export const deleteSite = async (id: string): Promise<void> => {
  await apiClient.delete(`/sites/${id}`)
}

// Plans
export const fetchPlans = async (siteId?: string): Promise<Plan[]> => {
  const params = siteId ? { site_id: siteId } : {}
  const response = await apiClient.get<Plan[]>('/plans', { params })
  return response.data
}

export const fetchPlan = async (id: string): Promise<Plan> => {
  const response = await apiClient.get<Plan>(`/plans/${id}`)
  return response.data
}

export const createPlan = async (data: CreatePlanRequest): Promise<Plan> => {
  const response = await apiClient.post<Plan>('/plans', data)
  return response.data
}

export const updatePlan = async (id: string, data: CreatePlanRequest): Promise<Plan> => {
  const response = await apiClient.put<Plan>(`/plans/${id}`, data)
  return response.data
}

export const deletePlan = async (id: string): Promise<void> => {
  await apiClient.delete(`/plans/${id}`)
}

// Sensors
export const fetchSensors = async (planId?: string): Promise<Sensor[]> => {
  const params = planId ? { plan_id: planId } : {}
  const response = await apiClient.get<Sensor[]>('/sensors', { params })
  return response.data
}

export const fetchSensor = async (id: string): Promise<Sensor> => {
  const response = await apiClient.get<Sensor>(`/sensors/${id}`)
  return response.data
}

export const createSensor = async (data: CreateSensorRequest): Promise<Sensor> => {
  const response = await apiClient.post<Sensor>('/sensors', data)
  return response.data
}

export const updateSensor = async (id: string, data: CreateSensorRequest): Promise<Sensor> => {
  const response = await apiClient.put<Sensor>(`/sensors/${id}`, data)
  return response.data
}

export const deleteSensor = async (id: string): Promise<void> => {
  await apiClient.delete(`/sensors/${id}`)
}
