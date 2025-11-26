<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
import EffectivePermissions from '@/components/EffectivePermissions.vue'
import InheritanceViewer from '@/components/permissions/InheritanceViewer.vue'
import PermissionMatrix from '@/components/permissions/PermissionMatrix.vue'
import { ref } from 'vue'

const activeTab = ref<'effective' | 'inheritance' | 'matrix'>('inheritance')
</script>

<template>
  <AppLayout>
    <div class="container mx-auto px-4 py-8">
      <div class="bg-white rounded-lg shadow-md overflow-hidden">
        <!-- Tabs -->
        <div class="border-b border-gray-200">
          <nav class="flex -mb-px">
            <button
              @click="activeTab = 'inheritance'"
              :class="[
                'py-4 px-6 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'inheritance'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              Permission Inheritance
            </button>
            <button
              @click="activeTab = 'effective'"
              :class="[
                'py-4 px-6 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'effective'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              Effective Permissions
            </button>
            <button
              @click="activeTab = 'matrix'"
              :class="[
                'py-4 px-6 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'matrix'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              Permission Matrix
            </button>
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="p-6">
          <InheritanceViewer v-if="activeTab === 'inheritance'" />
          <EffectivePermissions v-else-if="activeTab === 'effective'" />
          <PermissionMatrix v-else-if="activeTab === 'matrix'" />
        </div>
      </div>
    </div>
  </AppLayout>
</template>
