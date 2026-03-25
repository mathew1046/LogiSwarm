<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  reportId: {
    type: String,
    default: null
  },
  content: {
    type: String,
    default: ''
  }
})

const route = useRoute()
const loading = ref(false)
const error = ref(null)
const report = ref(null)
const activeSection = ref(null)

const sections = computed(() => {
  if (!report.value?.content && !props.content) return []
  
  const content = report.value?.content || props.content
  const lines = content.split('\n')
  const result = []
  let currentSection = null
  let currentContent = []
  
  lines.forEach(line => {
    if (line.startsWith('## ')) {
      if (currentSection) {
        result.push({ title: currentSection, content: currentContent.join('\n') })
      }
      currentSection = line.replace('## ', '').trim()
      currentContent = []
    } else if (currentSection) {
      currentContent.push(line)
    }
  })
  
  if (currentSection) {
    result.push({ title: currentSection, content: currentContent.join('\n') })
  }
  
  return result
})

async function fetchReport(id) {
  loading.value = true
  error.value = null
  try {
    const response = await fetch(`/api/reports/${id}`)
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error)
    }
    report.value = data.data
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function scrollToSection(index) {
  activeSection.value = index
  const element = document.getElementById(`section-${index}`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' })
  }
}

onMounted(() => {
  const id = props.reportId || route.params.reportId
  if (id && !props.content) {
    fetchReport(id)
  }
})

watch(() => props.reportId, (newId) => {
  if (newId && !props.content) {
    fetchReport(newId)
  }
})
</script>

<template>
  <div class="report-viewer">
    <div v-if="loading" class="loading">
      <div class="loading__spinner"></div>
    </div>

    <div v-else-if="error" class="error-state">
      <p class="error-message">{{ error }}</p>
      <button class="btn btn--primary" @click="fetchReport(reportId)">Retry</button>
    </div>

    <div v-else class="report-content">
      <nav class="report-toc">
        <h4>Contents</h4>
        <ul>
          <li 
            v-for="(section, index) in sections" 
            :key="index"
            :class="{ active: activeSection === index }"
            @click="scrollToSection(index)"
          >
            {{ section.title }}
          </li>
        </ul>
      </nav>

      <article class="report-body">
        <header v-if="report" class="report-header">
          <h1>{{ report.disruption_id ? `Disruption Report` : 'Analysis Report' }}</h1>
          <div class="report-meta">
            <span class="meta-item">
              <strong>Generated:</strong> {{ new Date(report.generated_at).toLocaleString() }}
            </span>
            <span v-if="report.disruption_id" class="meta-item">
              <strong>Disruption:</strong> {{ report.disruption_id }}
            </span>
          </div>
        </header>

        <div class="report-text" v-html="report?.content || content"></div>

        <div v-if="sections.length === 0 && !report?.content" class="empty-state">
          <p>No report content available</p>
        </div>
      </article>
    </div>

    <div class="report-actions">
      <button class="btn btn--secondary" @click="window.print()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2M6 14h12v8H6z" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Print
      </button>
    </div>
  </div>
</template>

<style scoped>
.report-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.report-content {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: var(--spacing-6);
  flex: 1;
  overflow: hidden;
}

.report-toc {
  background-color: var(--color-surface);
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
  padding: var(--spacing-4);
}

.report-toc h4 {
  margin-bottom: var(--spacing-3);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.report-toc ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.report-toc li {
  padding: var(--spacing-2) var(--spacing-3);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.report-toc li:hover {
  background-color: var(--color-bg-secondary);
  color: var(--color-text);
}

.report-toc li.active {
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
}

.report-body {
  overflow-y: auto;
  padding: var(--spacing-6);
}

.report-header {
  margin-bottom: var(--spacing-6);
  padding-bottom: var(--spacing-4);
  border-bottom: 1px solid var(--color-border);
}

.report-header h1 {
  margin-bottom: var(--spacing-2);
}

.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-4);
}

.meta-item {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.report-text {
  line-height: 1.7;
}

.report-text :deep(h1) {
  font-size: var(--text-2xl);
  margin-bottom: var(--spacing-4);
}

.report-text :deep(h2) {
  font-size: var(--text-xl);
  margin-top: var(--spacing-6);
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-2);
  border-bottom: 1px solid var(--color-border);
}

.report-text :deep(h3) {
  font-size: var(--text-lg);
  margin-top: var(--spacing-4);
  margin-bottom: var(--spacing-2);
}

.report-text :deep(p) {
  margin-bottom: var(--spacing-3);
}

.report-text :deep(ul) {
  margin-bottom: var(--spacing-3);
  padding-left: var(--spacing-6);
}

.report-text :deep(li) {
  margin-bottom: var(--spacing-1);
}

.report-text :deep(code) {
  background-color: var(--color-bg-secondary);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.report-text :deep(pre) {
  background-color: var(--color-bg-secondary);
  padding: var(--spacing-4);
  border-radius: var(--radius-md);
  overflow-x: auto;
}

.report-actions {
  display: flex;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  text-align: center;
}

.error-message {
  color: var(--color-error);
  margin-bottom: var(--spacing-4);
}

@media print {
  .report-toc,
  .report-actions {
    display: none;
  }
  
  .report-content {
    display: block;
  }
  
  .report-body {
    padding: 0;
  }
}
</style>