<script setup>
</script>

<template>
  <div class="skeleton-report">
    <div class="skeleton-report__header">
      <div class="skeleton-line skeleton-line--xl"></div>
      <div class="skeleton-line skeleton-line--md"></div>
    </div>
    <div class="skeleton-report__content">
      <div class="skeleton-line"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line skeleton-line--lg"></div>
      <div class="skeleton-line"></div>
      <div class="skeleton-line skeleton-line--md"></div>
    </div>
    <div class="skeleton-report__sidebar">
      <div class="suggestion-skeleton"></div>
      <div class="suggestion-skeleton"></div>
      <div class="suggestion-skeleton"></div>
    </div>
  </div>
</template>

<style scoped>
.skeleton-report {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: var(--spacing-6);
}

.skeleton-report__header {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-4);
}

.skeleton-report__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.skeleton-report__sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.skeleton-line {
  height: 16px;
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

.skeleton-line--md {
  width: 70%;
}

.skeleton-line--lg {
  width: 85%;
}

.skeleton-line--xl {
  width: 95%;
  height: 32px;
}

.suggestion-skeleton {
  height: 60px;
  background: linear-gradient(
    90deg,
    var(--color-bg-tertiary) 25%,
    var(--color-bg-secondary) 50%,
    var(--color-bg-tertiary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
  border-radius: var(--radius-md);
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