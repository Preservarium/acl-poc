// Resource API client for sites, plans, sensors, alarms, alerts, and brokers
import apiClient from './client'
import type {
  Site,
  Plan,
  Sensor,
  Alarm,
  Alert,
  Broker,
  CreateSiteRequest,
  CreatePlanRequest,
  CreateSensorRequest,
  CreateAlarmRequest,
  CreateAlertRequest,
  CreateBrokerRequest
} from '@/types'

// Sites
export const fetchSites = async (): Promise<Site[]> => {
  const response = await apiClient.get<Site[]>('/sites')
  return response.data
}

export const fetchSite = async (id: string, includePermissions = false): Promise<Site> => {
  const response = await apiClient.get<Site>(`/sites/${id}`, {
    params: { include_permissions: includePermissions }
  })
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

export const fetchSiteAdmins = async (id: string): Promise<any[]> => {
  const response = await apiClient.get<any[]>(`/sites/${id}/admins`)
  return response.data
}

// Plans
export const fetchPlans = async (siteId?: string): Promise<Plan[]> => {
  const params = siteId ? { site_id: siteId } : {}
  const response = await apiClient.get<Plan[]>('/plans', { params })
  return response.data
}

export const fetchPlan = async (id: string, includePermissions = false): Promise<Plan> => {
  const response = await apiClient.get<Plan>(`/plans/${id}`, {
    params: { include_permissions: includePermissions }
  })
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

export const fetchSensor = async (id: string, includePermissions = false): Promise<Sensor> => {
  const response = await apiClient.get<Sensor>(`/sensors/${id}`, {
    params: { include_permissions: includePermissions }
  })
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

// Alarms
export const fetchAlarms = async (sensorId?: string): Promise<Alarm[]> => {
  const params = sensorId ? { sensor_id: sensorId } : {}
  const response = await apiClient.get<Alarm[]>('/alarms', { params })
  return response.data
}

export const fetchAlarm = async (id: string, includePermissions = false): Promise<Alarm> => {
  const response = await apiClient.get<Alarm>(`/alarms/${id}`, {
    params: { include_permissions: includePermissions }
  })
  return response.data
}

export const createAlarm = async (data: CreateAlarmRequest): Promise<Alarm> => {
  const response = await apiClient.post<Alarm>('/alarms', data)
  return response.data
}

export const updateAlarm = async (id: string, data: CreateAlarmRequest): Promise<Alarm> => {
  const response = await apiClient.put<Alarm>(`/alarms/${id}`, data)
  return response.data
}

export const deleteAlarm = async (id: string): Promise<void> => {
  await apiClient.delete(`/alarms/${id}`)
}

// Alerts
export const fetchAlerts = async (alarmId?: string): Promise<Alert[]> => {
  const params = alarmId ? { alarm_id: alarmId } : {}
  const response = await apiClient.get<Alert[]>('/alerts', { params })
  return response.data
}

export const fetchAlert = async (id: string, includePermissions = false): Promise<Alert> => {
  const response = await apiClient.get<Alert>(`/alerts/${id}`, {
    params: { include_permissions: includePermissions }
  })
  return response.data
}

export const createAlert = async (data: CreateAlertRequest): Promise<Alert> => {
  const response = await apiClient.post<Alert>('/alerts', data)
  return response.data
}

export const updateAlert = async (id: string, data: CreateAlertRequest): Promise<Alert> => {
  const response = await apiClient.put<Alert>(`/alerts/${id}`, data)
  return response.data
}

export const deleteAlert = async (id: string): Promise<void> => {
  await apiClient.delete(`/alerts/${id}`)
}

// Brokers
export const fetchBrokers = async (planId?: string): Promise<Broker[]> => {
  const params = planId ? { plan_id: planId } : {}
  const response = await apiClient.get<Broker[]>('/brokers', { params })
  return response.data
}

export const fetchBroker = async (id: string, includePermissions = false): Promise<Broker> => {
  const response = await apiClient.get<Broker>(`/brokers/${id}`, {
    params: { include_permissions: includePermissions }
  })
  return response.data
}

export const createBroker = async (data: CreateBrokerRequest): Promise<Broker> => {
  const response = await apiClient.post<Broker>('/brokers', data)
  return response.data
}

export const updateBroker = async (id: string, data: CreateBrokerRequest): Promise<Broker> => {
  const response = await apiClient.put<Broker>(`/brokers/${id}`, data)
  return response.data
}

export const deleteBroker = async (id: string): Promise<void> => {
  await apiClient.delete(`/brokers/${id}`)
}
