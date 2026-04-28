<script setup>
defineProps({
  icon: { type: String, default: 'check' },
  title: { type: String, default: 'No data' },
  message: { type: String, default: 'No items to display' }
})

const iconPaths = {
  check: 'M22 11.08V12a10 10 0 11-5.17-8.77M22 4L12 14.01 9 11.01',
  inbox: 'M22 12 16 12 14 15 10 15 8 12 2 12M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z',
  empty: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zM8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01'
}
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path :d="iconPaths[icon] || iconPaths.empty" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-message">{{ message }}</p>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  text-align: center;
}

.empty-icon {
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-4);
  opacity: 0.5;
}

.empty-title {
  font-size: var(--text-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-2);
  color: var(--color-text);
}

.empty-message {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  max-width: 300px;
  line-height: var(--leading-relaxed);
}
</style>
