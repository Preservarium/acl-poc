<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import PermissionList from '@/components/PermissionList.vue'
import { fetchBroker, fetchPlan } from '@/api/resources'
import { fetchResourcePermissions } from '@/api/permissions'
import type { Broker, Plan, Permission } from '@/types'

const route = useRoute()
const router = useRouter()

const brokerId = computed(() => route.params.id as string)
const broker = ref<Broker | null>(null)
const plan = ref<Plan | null>(null)
const permissions = ref<Permission[]>([])

const loading = ref(false)
const error = ref<string | null>(null)

const activeTab = ref<'overview' | 'permissions'>('overview')

const loadBrokerDetails = async () => {
  loading.value = true
  error.value = null

  try {
    const brokerData = await fetchBroker(brokerId.value, true)
    broker.value = brokerData

    // Load plan details
    if (brokerData.plan_id) {
      const planData = await fetchPlan(brokerData.plan_id)
      plan.value = planData
    }

    // Load permissions if on permissions tab
    if (activeTab.value === 'permissions') {
      await loadPermissions()
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load broker details'
  } finally {
    loading.value = false
  }
}

const loadPermissions = async () => {
  if (!broker.value) return

  try {
    permissions.value = await fetchResourcePermissions('broker', broker.value.id)
  } catch (err: any) {
    console.error('Failed to load permissions:', err)
  }
}

onMounted(() => {
  loadBrokerDetails()
})
</script>

<template>
  <AppLayout>
    <div v-if="loading" class="text-center py-8">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      <p class="mt-2 text-gray-600">Loading broker details...</p>
    </div>

    <div v-else-if="error" class="text-center py-8 text-red-600">
      {{ error }}
      <button @click="loadBrokerDetails" class="ml-2 text-blue-600 hover:underline">
        Retry
      </button>
    </div>

    <div v-else-if="broker" class="space-y-6">
      <!-- Header -->
      <div class="bg-white shadow rounded-lg p-6">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-3xl font-bold text-gray-900 flex items-center gap-2">
              📶 {{ broker.name }}
            </h1>
            <p class="text-sm text-gray-600 mt-2">
              Protocol: <span class="font-medium">{{ broker.protocol }}</span>
            </p>
            <p v-if="plan" class="text-sm text-gray-600 mt-1">
              Plan: <router-link :to="`/plans/${plan.id}`" class="text-blue-600 hover:underline">{{ plan.name }}</router-link>
            </p>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="bg-white shadow rounded-lg">
        <div class="border-b border-gray-200">
          <nav class="flex -mb-px">
            <button
              @click="activeTab = 'overview'"
              :class="[
                'py-4 px-6 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'overview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              Overview
            </button>
            <button
              @click="activeTab = 'permissions'; loadPermissions()"
              :class="[
                'py-4 px-6 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'permissions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              🔐 Permissions
            </button>
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="p-6">
          <!-- Overview Tab -->
          <div v-if="activeTab === 'overview'" class="space-y-6">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Broker ID</label>
                <p class="mt-1 text-sm text-gray-900">{{ broker.id }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Protocol</label>
                <p class="mt-1 text-sm text-gray-900">{{ broker.protocol }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Created By</label>
                <p class="mt-1 text-sm text-gray-900">{{ broker.created_by }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Created At</label>
                <p class="mt-1 text-sm text-gray-900">{{ new Date(broker.created_at).toLocaleString() }}</p>
              </div>
            </div>
          </div>

          <!-- Permissions Tab -->
          <div v-if="activeTab === 'permissions'">
            <PermissionList
              :permissions="permissions"
              :resource-type="'broker'"
              :resource-id="broker.id"
              :resource-name="broker.name"
              @refresh="loadPermissions"
            />
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
