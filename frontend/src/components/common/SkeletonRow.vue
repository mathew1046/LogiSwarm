<script setup>
</script>

<template>
  <div class="skeleton-row">
    <div class="skeleton-cell skeleton-cell--sm"></div>
    <div class="skeleton-cell skeleton-cell--lg"></div>
    <div class="skeleton-cell skeleton-cell--md"></div>
    <div class="skeleton-cell skeleton-cell--md"></div>
    <div class="skeleton-cell skeleton-cell--sm"></div>
  </div>
</template>

<style scoped>
.skeleton-row {
  display: grid;
  grid-template-columns: 1fr 2fr 1.5fr 1.5fr 1fr;
  gap: var(--spacing-4);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
}

.skeleton-cell {
  height: 20px;
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

.skeleton-cell--sm {
  width: 60%;
}

.skeleton-cell--md {
  width: 80%;
}

.skeleton-cell--lg {
  width: 90%;
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