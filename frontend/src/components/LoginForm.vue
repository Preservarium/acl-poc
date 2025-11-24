<template>
  <div class="card max-w-md mx-auto">
    <h2 class="card-header text-center">Sign In</h2>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label for="username" class="label">Username</label>
        <input
          id="username"
          v-model="form.username"
          type="text"
          class="input"
          placeholder="Enter your username"
          required
          :disabled="loading"
        />
      </div>

      <div>
        <label for="password" class="label">Password</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          class="input"
          placeholder="Enter your password"
          required
          :disabled="loading"
        />
      </div>

      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>

      <button type="submit" class="btn-primary w-full" :disabled="loading">
        <span v-if="loading" class="flex items-center justify-center">
          <span class="spinner w-4 h-4 mr-2"></span>
          Signing in...
        </span>
        <span v-else>Sign In</span>
      </button>
    </form>

    <div class="mt-6 pt-6 border-t border-gray-200">
      <p class="text-sm text-gray-600 text-center">
        Demo users: alice/password, bob/password
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const errorMessage = ref('')

async function handleSubmit() {
  if (!form.username || !form.password) {
    errorMessage.value = 'Please enter both username and password'
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.login({
      username: form.username,
      password: form.password
    })

    // Redirect to the page they were trying to access, or dashboard
    const redirect = route.query.redirect as string
    router.push(redirect || '/dashboard')
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
