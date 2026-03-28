// LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
// Copyright (C) 2025 LogiSwarm Contributors
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAlertStore } from '@/stores/alert'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const alertStore = useAlertStore()
const expandedAlert = ref(null)

const unreadCount = computed(() => alertStore.unreadCount)
const alerts = computed(() => alertStore.alerts)

function getSeverityIcon(severity) {
  const icons = {
    CRITICAL: '🔴',
    HIGH: '🟠',
    MEDIUM: '🟡',
    LOW: '🟢'
  }
  return icons[severity] || '⚪'
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  return date.toLocaleDateString()
}

function handleAction(alertId, action) {
  if (action === 'accept' || action === 'dismiss') {
    alertStore.handleAlert(alertId, action)
  } else if (action === 'escalate') {
    alertStore.handleAlert(alertId, action)
  }
  expandedAlert.value = null
}

function dismissAlert(alertId) {
  alertStore.dismissAlert(alertId)
}

function markAsRead(alertId) {
  alertStore.markAsRead(alertId)
}

function markAllRead() {
  alertStore.markAllAsRead()
}
</script>

<template>
  <Teleport to="body">
    <div v-if="isOpen" class="notification-overlay" @click="emit('close')">
      <div class="notification-panel" @click.stop>
        <div class="notification-header">
          <h3>Notifications</h3>
          <div class="notification-actions">
            <button class="btn btn--sm btn--secondary" @click="markAllRead" :disabled="unreadCount === 0">
              Mark all read
            </button>
            <button class="close-btn" @click="emit('close')">×</button>
          </div>
        </div>

        <div class="notification-list">
          <div v-if="alerts.length === 0" class="empty-state">
            <p>No notifications</p>
          </div>

          <div 
            v-for="alert in alerts.slice(0, 50)" 
            :key="alert.id"
            :class="['notification-item', { unread: !alert.read, expanded: expandedAlert === alert.id }]"
            @click="expandedAlert === alert.id ? expandedAlert = null : expandedAlert = alert.id"
          >
            <div class="notification-item__header">
              <span class="notification-icon">{{ getSeverityIcon(alert.severity) }}</span>
              <div class="notification-item__meta">
                <span class="notification-region">{{ alert.region_id }}</span>
                <span class="notification-time">{{ formatTime(alert.timestamp) }}</span>
              </div>
              <span :class="['severity-badge', 'severity-' + (alert.severity || 'low').toLowerCase()]">
                {{ alert.severity }}
              </span>
            </div>
            
            <p class="notification-summary">{{ alert.summary }}</p>
            
            <div v-if="expandedAlert === alert.id" class="notification-detail">
              <p v-if="alert.details">{{ alert.details }}</p>
              <div class="notification-buttons">
                <button class="btn btn--sm btn--primary" @click.stop="handleAction(alert.id, 'accept')">
                  Accept
                </button>
                <button class="btn btn--sm btn--secondary" @click.stop="handleAction(alert.id, 'dismiss')">
                  Dismiss
                </button>
                <button class="btn btn--sm btn--secondary" @click.stop="dismissAlert(alert.id)">
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.notification-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.notification-panel {
  width: 400px;
  max-width: 100%;
  height: 100%;
  background-color: var(--color-surface);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
}

.notification-header h3 {
  margin: 0;
}

.notification-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  font-size: var(--text-xl);
  cursor: pointer;
  color: var(--color-text-secondary);
}

.close-btn:hover {
  color: var(--color-text);
}

.notification-list {
  flex: 1;
  overflow-y: auto;
}

.notification-item {
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.notification-item:hover {
  background-color: var(--color-bg-secondary);
}

.notification-item.unread {
  background-color: rgba(59, 130, 246, 0.05);
}

.notification-item__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
}

.notification-icon {
  font-size: var(--text-lg);
}

.notification-item__meta {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.notification-region {
  font-weight: 600;
  font-size: var(--text-sm);
}

.notification-time {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.severity-badge {
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 500;
}

.severity-low { background-color: var(--color-low); color: white; }
.severity-medium { background-color: var(--color-medium); color: white; }
.severity-high { background-color: var(--color-high); color: white; }
.severity-critical { background-color: var(--color-critical); color: white; }

.notification-summary {
  font-size: var(--text-sm);
  margin: 0;
  color: var(--color-text);
}

.notification-detail {
  margin-top: var(--spacing-3);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border);
}

.notification-buttons {
  display: flex;
  gap: var(--spacing-2);
  margin-top: var(--spacing-2);
}
</style>