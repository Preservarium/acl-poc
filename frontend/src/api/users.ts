// Users and Groups API client
import apiClient from './client'
import type { User, Group, EffectivePermissionsResponse } from '@/types'

// Users
export const fetchUsers = async (): Promise<User[]> => {
  const response = await apiClient.get<User[]>('/users')
  return response.data
}

export const fetchUser = async (id: string): Promise<User> => {
  const response = await apiClient.get<User>(`/users/${id}`)
  return response.data
}

export const createUser = async (data: { username: string; password: string; is_admin?: boolean }): Promise<User> => {
  const response = await apiClient.post<User>('/users', data)
  return response.data
}

export const deleteUser = async (id: string): Promise<void> => {
  await apiClient.delete(`/users/${id}`)
}

// Groups
export const fetchGroups = async (): Promise<Group[]> => {
  const response = await apiClient.get<Group[]>('/groups')
  return response.data
}

export const fetchGroup = async (id: string): Promise<Group> => {
  const response = await apiClient.get<Group>(`/groups/${id}`)
  return response.data
}

export const fetchGroupMembers = async (groupId: string): Promise<User[]> => {
  const response = await apiClient.get<User[]>(`/groups/${groupId}/members`)
  return response.data
}

// Effective Permissions
export const fetchUserEffectivePermissions = async (userId: string): Promise<EffectivePermissionsResponse> => {
  const response = await apiClient.get<EffectivePermissionsResponse>(`/users/${userId}/effective-permissions`)
  return response.data
}
