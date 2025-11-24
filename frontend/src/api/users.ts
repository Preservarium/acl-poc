// Users and Groups API client
import apiClient from './client'
import type { User, Group } from '@/types'

// Users
export const fetchUsers = async (): Promise<User[]> => {
  const response = await apiClient.get<User[]>('/users')
  return response.data
}

export const fetchUser = async (id: string): Promise<User> => {
  const response = await apiClient.get<User>(`/users/${id}`)
  return response.data
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
