// API client setup with Axios
import axios, { AxiosError } from 'axios'
import type { ApiError, PermissionDeniedDetail } from '@/types'
import router from '@/router'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError | PermissionDeniedDetail>) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    } else if (error.response?.status === 403) {
      // Permission Denied - redirect to access denied page with details
      const data = error.response.data as any

      // Check if this is a detailed permission error
      if (data && typeof data === 'object' && 'required_permission' in data) {
        const permissionDetails = data as PermissionDeniedDetail

        // Navigate to access denied page with permission details in state
        router.push({
          name: 'AccessDenied',
          state: {
            permissionDetails
          },
          query: {
            resource_type: permissionDetails.resource_type,
            resource_id: permissionDetails.resource_id,
            action: permissionDetails.required_permission
          }
        })
      } else {
        // Fallback for simple 403 errors without details
        router.push({
          name: 'AccessDenied'
        })
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
