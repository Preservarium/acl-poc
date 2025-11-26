<template>
  <div class="site-overview">
    <div class="overview-section">
      <h2 class="section-title">Site Information</h2>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Name</span>
          <div class="info-value">{{ site?.name }}</div>
        </div>
        <div class="info-item">
          <span class="info-label">Created By</span>
          <div class="info-value">{{ site?.created_by }}</div>
        </div>
        <div class="info-item">
          <span class="info-label">Created At</span>
          <div class="info-value">{{ formatDate(site?.created_at) }}</div>
        </div>
        <div class="info-item">
          <span class="info-label">Total Plans</span>
          <div class="info-value">{{ planCount }}</div>
        </div>
      </div>
    </div>

    <div v-if="administrators.length > 0" class="overview-section">
      <h2 class="section-title">Administrators</h2>
      <p class="section-description">Users with 'manage' permission on this site</p>
      <div class="administrators-list">
        <div
          v-for="admin in administrators"
          :key="admin.id"
          class="admin-item"
        >
          <div class="admin-info">
            <span class="admin-icon">👤</span>
            <div>
              <div class="admin-name">{{ admin.grantee_name || admin.grantee_id }}</div>
              <div class="admin-source">via {{ admin.resource_name || 'this site' }}</div>
            </div>
          </div>
          <span class="admin-badge">manage</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Site, Permission } from '@/types'

const props = defineProps<{
  site: Site | null
  planCount: number
  administrators: Permission[]
}>()

const formatDate = (dateString?: string) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleString()
}
</script>

<style scoped>
.site-overview {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.overview-section {
  background: white;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 1rem;
}

.section-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.info-value {
  font-size: 1rem;
  font-weight: 500;
  color: #111827;
}

.administrators-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.admin-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: #faf5ff;
  border: 1px solid #e9d5ff;
  border-radius: 0.5rem;
  transition: all 0.15s ease;
}

.admin-item:hover {
  border-color: #d8b4fe;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
}

.admin-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.admin-icon {
  font-size: 1.5rem;
  line-height: 1;
}

.admin-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.admin-source {
  font-size: 0.75rem;
  color: #6b7280;
}

.admin-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 9999px;
  background: #7c3aed;
  color: white;
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .admin-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
}
</style>
