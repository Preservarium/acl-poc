<template>
  <div class="audit-log-view">
    <div class="header">
      <h1>Audit Logs</h1>
      <p class="subtitle">View permission change history and access attempts</p>
    </div>

    <div class="filters-card">
      <div class="filters">
        <div class="filter-group">
          <label for="action-filter">Action</label>
          <select id="action-filter" v-model="filters.action" @change="loadAuditLogs">
            <option value="">All Actions</option>
            <option value="permission_granted">Permission Granted</option>
            <option value="permission_revoked">Permission Revoked</option>
            <option value="permission_denied">Permission Denied</option>
            <option value="permission_expired">Permission Expired</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="user-filter">User</label>
          <select id="user-filter" v-model="filters.user_id" @change="loadAuditLogs">
            <option value="">All Users</option>
            <option v-for="user in users" :key="user.id" :value="user.id">
              {{ user.username }}
            </option>
          </select>
        </div>

        <div class="filter-group">
          <label for="days-filter">Time Range</label>
          <select id="days-filter" v-model.number="filters.days" @change="loadAuditLogs">
            <option :value="1">Last 24 hours</option>
            <option :value="7">Last 7 days</option>
            <option :value="30">Last 30 days</option>
            <option :value="90">Last 90 days</option>
          </select>
        </div>

        <div class="filter-group">
          <label for="page-size-filter">Items per page</label>
          <select id="page-size-filter" v-model.number="filters.page_size" @change="loadAuditLogs">
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="200">200</option>
          </select>
        </div>

        <button class="reset-btn" @click="resetFilters">
          Reset Filters
        </button>
      </div>
    </div>

    <div class="content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading audit logs...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <div class="error-icon">!</div>
        <p>{{ error }}</p>
        <button @click="loadAuditLogs">Retry</button>
      </div>

      <div v-else-if="auditLogs.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <p>No audit logs found</p>
        <p class="empty-hint">Try adjusting your filters</p>
      </div>

      <div v-else class="logs-container">
        <div class="logs-header">
          <div class="header-col">Timestamp</div>
          <div class="header-col">Action</div>
          <div class="header-col">Details</div>
        </div>

        <div class="logs-list">
          <AuditLogEntry
            v-for="log in auditLogs"
            :key="log.id"
            :log="log"
          />
        </div>

        <div v-if="auditLogs.length > 0" class="pagination">
          <button
            :disabled="filters.page === 1"
            @click="changePage(filters.page - 1)"
          >
            Previous
          </button>
          <span class="page-info">Page {{ filters.page }}</span>
          <button
            :disabled="auditLogs.length < filters.page_size"
            @click="changePage(filters.page + 1)"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchAuditLogs, type AuditLog, type AuditLogFilters } from '@/api/audit'
import { fetchUsers } from '@/api/users'
import AuditLogEntry from '@/components/audit/AuditLogEntry.vue'

interface User {
  id: string
  username: string
}

const auditLogs = ref<AuditLog[]>([])
const users = ref<User[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const filters = ref<AuditLogFilters>({
  action: '',
  user_id: '',
  days: 7,
  page: 1,
  page_size: 50
})

async function loadAuditLogs() {
  loading.value = true
  error.value = null

  try {
    const logs = await fetchAuditLogs(filters.value)
    auditLogs.value = logs
  } catch (err: any) {
    console.error('Failed to load audit logs:', err)
    error.value = err.response?.data?.detail || 'Failed to load audit logs'
  } finally {
    loading.value = false
  }
}

async function loadUsers() {
  try {
    const userList = await fetchUsers()
    users.value = userList
  } catch (err) {
    console.error('Failed to load users:', err)
  }
}

function changePage(page: number) {
  filters.value.page = page
  loadAuditLogs()
}

function resetFilters() {
  filters.value = {
    action: '',
    user_id: '',
    days: 7,
    page: 1,
    page_size: 50
  }
  loadAuditLogs()
}

onMounted(() => {
  loadAuditLogs()
  loadUsers()
})
</script>

<style scoped>
.audit-log-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.header {
  margin-bottom: 2rem;
}

.header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

.filters-card {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 150px;
}

.filter-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.filter-group select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  background-color: white;
  cursor: pointer;
}

.filter-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.reset-btn {
  padding: 0.5rem 1rem;
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover {
  background-color: #e5e7eb;
}

.content {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-state {
  color: #991b1b;
}

.error-icon {
  width: 64px;
  height: 64px;
  background-color: #fee2e2;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 1rem;
}

.error-state button {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: #dc2626;
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
}

.empty-state {
  color: #6b7280;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-hint {
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.logs-container {
  display: flex;
  flex-direction: column;
}

.logs-header {
  display: grid;
  grid-template-columns: 180px 200px 1fr;
  gap: 1rem;
  padding: 1rem;
  background-color: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.logs-list {
  min-height: 200px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.pagination button {
  padding: 0.5rem 1rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.pagination button:hover:not(:disabled) {
  background-color: #2563eb;
}

.pagination button:disabled {
  background-color: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.875rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .audit-log-view {
    padding: 1rem;
  }

  .filters {
    flex-direction: column;
  }

  .filter-group {
    width: 100%;
  }

  .logs-header {
    display: none;
  }
}
</style>
