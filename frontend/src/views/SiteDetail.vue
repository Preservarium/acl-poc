<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import ResourceTabs from '@/components/ResourceTabs.vue'
import SiteOverview from '@/components/site/SiteOverview.vue'
import SitePlans from '@/components/site/SitePlans.vue'
import SitePermissions from '@/components/site/SitePermissions.vue'
import { fetchSite, deleteSite, fetchPlans, createPlan } from '@/api/resources'
import { fetchSensors, fetchAlarms, fetchBrokers } from '@/api/resources'
import { fetchResourcePermissions, revokePermission } from '@/api/permissions'
import type { Site, Plan, Permission, Sensor, Alarm, Broker } from '@/types'

const route = useRoute()
const router = useRouter()

const siteId = computed(() => route.params.id as string)
const site = ref<Site | null>(null)
const plans = ref<Plan[]>([])
const permissions = ref<Permission[]>([])

const loading = ref(false)
const error = ref<string | null>(null)

// Tab state - now supports route parameter
const activeTab = ref<string>(route.params.tab as string || 'overview')

// Plan counts (sensors, brokers, alarms per plan)
const planCounts = ref<Map<string, { sensors: number; brokers: number; alarms: number }>>(new Map())

// Create plan modal state
const showCreatePlanModal = ref(false)
const planForm = ref({
  name: ''
})
const creatingPlan = ref(false)
const createPlanError = ref<string | null>(null)

// Administrators (users with 'manage' permission)
const administrators = computed(() => {
  return permissions.value.filter(p =>
    p.grantee_type === 'user' &&
    p.permission === 'manage' &&
    p.resource_type === 'site' &&
    p.resource_id === siteId.value
  )
})

const loadSiteDetails = async () => {
  loading.value = true
  error.value = null

  try {
    const [siteData, plansData, permissionsData] = await Promise.all([
      fetchSite(siteId.value),
      fetchPlans(siteId.value),
      fetchResourcePermissions('site', siteId.value)
    ])

    site.value = siteData
    plans.value = plansData
    permissions.value = permissionsData

    // Load counts for each plan
    await loadPlanCounts()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load site details'
  } finally {
    loading.value = false
  }
}

const loadPlanCounts = async () => {
  const counts = new Map()

  for (const plan of plans.value) {
    try {
      const [sensors, brokers] = await Promise.all([
        fetchSensors(plan.id),
        fetchBrokers(plan.id)
      ])

      // Count total alarms across all sensors in this plan
      let totalAlarms = 0
      for (const sensor of sensors) {
        const alarms = await fetchAlarms(sensor.id)
        totalAlarms += alarms.length
      }

      counts.set(plan.id, {
        sensors: sensors.length,
        brokers: brokers.length,
        alarms: totalAlarms
      })
    } catch {
      counts.set(plan.id, { sensors: 0, brokers: 0, alarms: 0 })
    }
  }

  planCounts.value = counts
}

const openCreatePlanModal = () => {
  planForm.value = { name: '' }
  createPlanError.value = null
  showCreatePlanModal.value = true
}

const handleCreatePlan = async () => {
  if (!planForm.value.name.trim()) {
    createPlanError.value = 'Plan name is required'
    return
  }

  creatingPlan.value = true
  createPlanError.value = null

  try {
    await createPlan({
      name: planForm.value.name,
      site_id: siteId.value
    })

    await loadSiteDetails()
    showCreatePlanModal.value = false
  } catch (err: any) {
    createPlanError.value = err.response?.data?.detail || 'Failed to create plan'
  } finally {
    creatingPlan.value = false
  }
}

const handleViewPlan = (planId: string) => {
  // Navigate to plan detail view (to be created)
  router.push(`/plans/${planId}`)
}

const handleDeleteSite = async () => {
  if (!confirm(`Are you sure you want to delete "${site.value?.name}"? This action cannot be undone.`)) {
    return
  }

  try {
    await deleteSite(siteId.value)
    router.push('/resources')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to delete site'
  }
}

const handleRevokePermission = async (permissionId: string) => {
  if (!confirm('Are you sure you want to revoke this permission?')) {
    return
  }

  try {
    await revokePermission(permissionId)
    await loadSiteDetails()
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to revoke permission'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

onMounted(() => {
  loadSiteDetails()
})
</script>

<template>
  <AppLayout>
    <div class="container mx-auto px-4 py-8">
      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12 text-gray-500">
        Loading site details...
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-6">
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="loadSiteDetails"
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>

      <!-- Site Details -->
      <div v-else-if="site" class="space-y-6">
        <!-- Header with Breadcrumb -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <div class="flex items-center justify-between mb-4">
            <div class="flex items-center gap-3">
              <button
                @click="router.push('/resources')"
                class="text-gray-400 hover:text-gray-600 transition-colors"
              >
                Sites
              </button>
              <span class="text-gray-400">&rsaquo;</span>
              <span class="text-3xl">🏭</span>
              <h1 class="text-3xl font-bold text-gray-800">{{ site.name }}</h1>
            </div>
            <div class="flex gap-2">
              <button
                @click="router.push(`/sites/${siteId}/edit`)"
                class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              >
                Edit
              </button>
              <button
                @click="handleDeleteSite"
                class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>

        <!-- Tabbed Content -->
        <ResourceTabs
          :tabs="[
            { id: 'overview', label: 'Overview' },
            { id: 'plans', label: 'Plans', count: plans.length },
            { id: 'permissions', label: 'Permissions', icon: '🔐' }
          ]"
          v-model:activeTab="activeTab"
        >
          <template #overview>
            <SiteOverview
              :site="site"
              :plan-count="plans.length"
              :administrators="administrators"
            />
          </template>
          <template #plans>
            <SitePlans
              :plans="plans"
              :plan-counts="planCounts"
              @create-plan="openCreatePlanModal"
              @view-plan="handleViewPlan"
            />
          </template>
          <template #permissions>
            <SitePermissions
              :permissions="permissions"
              :loading="false"
              @revoke="handleRevokePermission"
            />
          </template>
        </ResourceTabs>
      </div>

      <!-- Create Plan Modal -->
      <Transition name="modal">
        <div
          v-if="showCreatePlanModal"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
          @click.self="showCreatePlanModal = false"
        >
          <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <!-- Header -->
            <div class="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 class="text-xl font-bold text-gray-800">Add New Plan</h2>
              <button
                @click="showCreatePlanModal = false"
                class="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                ×
              </button>
            </div>

            <!-- Content -->
            <div class="p-6">
              <!-- Error Message -->
              <div v-if="createPlanError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {{ createPlanError }}
              </div>

              <form @submit.prevent="handleCreatePlan" class="space-y-4">
                <!-- Name Field -->
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">
                    Plan Name
                  </label>
                  <input
                    v-model="planForm.name"
                    type="text"
                    required
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter plan name"
                  />
                </div>

                <!-- Buttons -->
                <div class="flex justify-end gap-3">
                  <button
                    type="button"
                    @click="showCreatePlanModal = false"
                    class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    :disabled="creatingPlan"
                    class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {{ creatingPlan ? 'Creating...' : 'Create Plan' }}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </AppLayout>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .bg-white,
.modal-leave-active .bg-white {
  transition: transform 0.3s ease;
}

.modal-enter-from .bg-white,
.modal-leave-to .bg-white {
  transform: scale(0.9);
}
</style>
