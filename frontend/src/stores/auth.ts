import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api/auth'
import type { User, LoginRequest } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const username = computed(() => user.value?.username || '')

  // Actions
  async function login(credentials: LoginRequest): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const response = await authAPI.login(credentials)
      token.value = response.access_token

      // Store token in localStorage
      localStorage.setItem('access_token', response.access_token)

      // Fetch current user data
      await fetchCurrentUser()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentUser(): Promise<void> {
    if (!token.value) {
      throw new Error('No token available')
    }

    try {
      user.value = await authAPI.getCurrentUser()
    } catch (err) {
      // If fetching user fails, clear the token
      logout()
      throw err
    }
  }

  function logout(): void {
    user.value = null
    token.value = null
    localStorage.removeItem('access_token')
    authAPI.logout()
  }

  async function initialize(): Promise<void> {
    // If there's a token in localStorage, try to fetch the user
    if (token.value) {
      try {
        await fetchCurrentUser()
      } catch {
        // Token is invalid, clear it
        logout()
      }
    }
  }

  return {
    // State
    user,
    token,
    loading,
    error,
    // Getters
    isAuthenticated,
    username,
    // Actions
    login,
    logout,
    fetchCurrentUser,
    initialize
  }
})
