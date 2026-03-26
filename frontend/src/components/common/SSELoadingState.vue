<script setup>
defineProps({
  message: { type: String, default: 'Connecting to live feed...' }
})
</script>

<template>
  <div class="sse-loading">
    <div class="sse-loading__dots">
      <span></span>
      <span></span>
      <span></span>
    </div>
    <p class="sse-loading__message">{{ message }}</p>
  </div>
</template>

<style scoped>
.sse-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  text-align: center;
}

.sse-loading__dots {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

.sse-loading__dots span {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-full);
  background-color: var(--color-primary);
  animation: bounce 1.4s ease-in-out infinite both;
}

.sse-loading__dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.sse-loading__dots span:nth-child(2) {
  animation-delay: -0.16s;
}

.sse-loading__message {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>