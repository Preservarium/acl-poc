// Groups API client
import apiClient from './client'
import type { Group, User, Permission } from '@/types'

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

export const fetchGroupPermissions = async (groupId: string): Promise<Permission[]> => {
  const response = await apiClient.get<Permission[]>(`/groups/${groupId}/permissions`)
  return response.data
}

export const addGroupMember = async (groupId: string, userId: string): Promise<void> => {
  await apiClient.post(`/groups/${groupId}/members/${userId}`)
}

export const removeGroupMember = async (groupId: string, userId: string): Promise<void> => {
  await apiClient.delete(`/groups/${groupId}/members/${userId}`)
}
