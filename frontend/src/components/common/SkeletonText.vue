<script setup>
defineProps({
  lines: { type: Number, default: 3 },
  lineHeight: { type: String, default: '16px' }
})
</script>

<template>
  <div class="skeleton skeleton-text">
    <div 
      v-for="i in lines" 
      :key="i"
      class="skeleton-line"
      :style="{ height: lineHeight }"
    ></div>
  </div>
</template>

<style scoped>
.skeleton-text {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.skeleton-line {
  background: linear-gradient(
    90deg,
    var(--color-bg-tertiary) 25%,
    var(--color-bg-secondary) 50%,
    var(--color-bg-tertiary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>