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

function getSeverityClass(severity) {
  return `badge--${(severity || 'low').toLowerCase()}`
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
      <div class="notification-panel glass--elevated" @click.stop>
        <div class="notification-header">
          <h3>Notifications</h3>
          <div class="notification-actions">
            <button class="btn btn--sm btn--secondary" @click="markAllRead" :disabled="unreadCount === 0">
              Mark all read
            </button>
            <button class="close-btn" @click="emit('close')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="notification-list">
          <div v-if="alerts.length === 0" class="empty-state">
            <p class="empty-state__text">No notifications</p>
          </div>

          <div
            v-for="alert in alerts.slice(0, 50)"
            :key="alert.id"
            :class="['notification-item', { unread: !alert.read, expanded: expandedAlert === alert.id }]"
            @click="expandedAlert === alert.id ? expandedAlert = null : expandedAlert = alert.id"
          >
            <div class="notification-item__header">
              <div class="notification-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
              </div>
              <div class="notification-item__meta">
                <span class="notification-region">{{ alert.region_id }}</span>
                <span class="notification-time text-mono">{{ formatTime(alert.timestamp) }}</span>
              </div>
              <span :class="['badge', getSeverityClass(alert.severity)]">
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
                <button class="btn btn--sm btn--ghost" @click.stop="dismissAlert(alert.id)">
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
  background-color: rgba(0, 0, 0, 0.6);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.notification-panel {
  width: 400px;
  max-width: 100%;
  height: 100%;
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
  font-size: var(--text-lg);
  font-weight: 600;
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
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background-color: var(--color-bg-tertiary);
  color: var(--color-text);
}

.notification-list {
  flex: 1;
  overflow-y: auto;
}

.notification-item {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.notification-item:hover {
  background-color: var(--color-bg-tertiary);
}

.notification-item.unread {
  background-color: rgba(59, 130, 246, 0.05);
  border-left: 2px solid var(--color-primary);
}

.notification-item__header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
}

.notification-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background-color: var(--color-bg-tertiary);
  color: var(--color-warning);
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
  color: var(--color-text-tertiary);
}

.notification-summary {
  font-size: var(--text-sm);
  margin: 0;
  color: var(--color-text-secondary);
  line-height: var(--leading-relaxed);
}

.notification-detail {
  margin-top: var(--spacing-3);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--color-border);
  animation: fadeIn 200ms ease;
}

.notification-buttons {
  display: flex;
  gap: var(--spacing-2);
  margin-top: var(--spacing-2);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
