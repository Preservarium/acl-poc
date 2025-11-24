// Auth API client
import apiClient from './client'
import type { LoginRequest, LoginResponse, User } from '@/types'

export const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/auth/login', credentials)
  return response.data
}

export const logout = async (): Promise<void> => {
  await apiClient.post('/auth/logout')
}

export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/auth/me')
  return response.data
}

// Export as authAPI for compatibility with existing code
export const authAPI = {
  login,
  logout,
  getCurrentUser
}
