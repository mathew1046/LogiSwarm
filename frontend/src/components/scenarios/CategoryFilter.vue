<script setup>
/**
 * CategoryFilter - Horizontal scrollable filter bar for scenario categories
 *
 * Props:
 *   categories: Array of { category: string, count: number } - categories with counts
 *   activeCategory: string | null - currently selected category (null = "All")
 *
 * Emits:
 *   filter: (category: string | null) => void - when a category is selected
 */

defineProps({
  categories: {
    type: Array,
    required: true,
    default: () => []
  },
  activeCategory: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['filter'])

function selectCategory(category) {
  emit('filter', category)
}

function formatCategoryName(category) {
  return category.charAt(0) + category.slice(1).toLowerCase()
}
</script>

<template>
  <div class="category-filter">
    <div class="category-filter__scroll">
      <button
        class="category-pill"
        :class="{ 'category-pill--active': activeCategory === null }"
        @click="selectCategory(null)"
      >
        <span class="category-pill__name">All</span>
        <span class="category-pill__count">
          {{ categories.reduce((sum, c) => sum + c.count, 0) }}
        </span>
      </button>

      <button
        v-for="{ category, count } in categories"
        :key="category"
        class="category-pill"
        :class="{ 'category-pill--active': activeCategory === category }"
        @click="selectCategory(category)"
      >
        <span class="category-pill__name">{{ formatCategoryName(category) }}</span>
        <span class="category-pill__count">{{ count }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.category-filter {
  position: relative;
  width: 100%;
}

.category-filter__scroll {
  display: flex;
  gap: var(--spacing-2);
  overflow-x: auto;
  padding: var(--spacing-1) 0;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}

.category-filter__scroll::-webkit-scrollbar {
  height: 4px;
}

.category-filter__scroll::-webkit-scrollbar-track {
  background: transparent;
}

.category-filter__scroll::-webkit-scrollbar-thumb {
  background-color: var(--color-border);
  border-radius: var(--radius-full);
}

.category-filter__scroll::-webkit-scrollbar-thumb:hover {
  background-color: var(--color-border-hover);
}

.category-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.category-pill:hover {
  background-color: var(--color-bg-tertiary);
  border-color: var(--color-border-hover);
  color: var(--color-text);
}

.category-pill--active {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-text-inverse);
}

.category-pill--active:hover {
  background-color: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
  color: var(--color-text-inverse);
}

.category-pill__name {
  font-weight: 500;
}

.category-pill__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--spacing-1);
  font-size: var(--text-xs);
  font-weight: 600;
  background-color: rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-full);
}

.category-pill:not(.category-pill--active) .category-pill__count {
  background-color: var(--color-bg-tertiary);
  color: var(--color-text-tertiary);
}

.category-pill--active .category-pill__count {
  background-color: rgba(255, 255, 255, 0.2);
}

/* Mobile: horizontal scroll indicator via gradient fade */
@media (max-width: 640px) {
  .category-filter {
    position: relative;
  }

  .category-filter::after {
    content: '';
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 40px;
    background: linear-gradient(to right, transparent, var(--color-bg));
    pointer-events: none;
  }
}
</style>
