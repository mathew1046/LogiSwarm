<script setup>
import { ref, computed } from 'vue'
import { useAgentStore } from '@/stores/agent'

const props = defineProps({
  regionId: {
    type: String,
    required: true
  },
  regionName: {
    type: String,
    default: ''
  }
})

const agentStore = useAgentStore()
const question = ref('')
const answer = ref('')
const sources = ref([])
const loading = ref(false)
const error = ref(null)
const currentRiskLevel = ref(null)
const currentConfidence = ref(null)

const hasAnswer = computed(() => answer.value && answer.value.length > 0)

const suggestedQuestions = [
  'What are the current risk factors in this region?',
  'What historical disruptions have occurred here?',
  'What mitigation strategies are recommended?',
  'How does this region connect to neighboring regions?',
  'What seasonal patterns should we watch for?'
]

async function submitQuestion(q) {
  const questionText = q || question.value
  if (!questionText || questionText.trim().length < 5) {
    error.value = 'Please enter a question with at least 5 characters.'
    return
  }

  loading.value = true
  error.value = null
  answer.value = ''
  sources.value = []

  try {
    const response = await fetch(`/api/agents/${props.regionId}/interview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: questionText })
    })
    const data = await response.json()
    
    if (data.error) {
      throw new Error(data.error)
    }

    answer.value = data.answer
    sources.value = data.sources || []
    currentRiskLevel.value = data.current_risk_level
    currentConfidence.value = data.current_confidence
    question.value = ''
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return 'Unknown date'
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div class="interview-panel">
    <div class="interview-header">
      <h3>Interview {{ regionName || regionId }}</h3>
      <div v-if="currentRiskLevel" class="current-status">
        <span class="status-label">Current Status:</span>
        <span :class="['status-badge', `status--${(currentRiskLevel || '').toLowerCase()}`]">
          {{ currentRiskLevel }}
        </span>
        <span v-if="currentConfidence !== null" class="confidence">
          ({{ (currentConfidence * 100).toFixed(0) }}% confidence)
        </span>
      </div>
    </div>

    <div class="suggested-questions">
      <span class="suggested-label">Suggested questions:</span>
      <div class="suggested-list">
        <button
          v-for="sq in suggestedQuestions"
          :key="sq"
          class="btn btn--sm btn--outline suggested-btn"
          @click="submitQuestion(sq)"
          :disabled="loading"
        >
          {{ sq }}
        </button>
      </div>
    </div>

    <div class="question-input">
      <textarea
        v-model="question"
        placeholder="Ask a question about this region..."
        rows="3"
        :disabled="loading"
        @keydown.ctrl.enter="submitQuestion()"
        @keydown.meta.enter="submitQuestion()"
      ></textarea>
      <button
        class="btn btn--primary submit-btn"
        @click="submitQuestion()"
        :disabled="loading || !question || question.trim().length < 5"
      >
        <span v-if="loading" class="loading-spinner"></span>
        <span v-else>Ask</span>
      </button>
    </div>

    <div v-if="error" class="error-message">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
      {{ error }}
    </div>

    <div v-if="hasAnswer" class="answer-section">
      <div class="answer-content">
        <p>{{ answer }}</p>
      </div>

      <div v-if="sources.length > 0" class="sources-section">
        <h4>Sources</h4>
        <div class="sources-list">
          <div v-for="(source, index) in sources" :key="index" class="source-item">
            <span class="source-severity" :class="`severity--${(source.severity || 'low').toLowerCase()}`">
              {{ source.severity || 'Info' }}
            </span>
            <span class="source-content">{{ source.content }}</span>
            <span class="source-date">{{ formatDate(source.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.interview-panel {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  padding: var(--spacing-4);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.interview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.interview-header h3 {
  margin: 0;
}

.current-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.status-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.status-badge {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
}

.status--low { background-color: var(--color-success-bg, #dcfce7); color: var(--color-success, #16a34a); }
.status--medium { background-color: var(--color-warning-bg, #fef3c7); color: var(--color-warning, #d97706); }
.status--high { background-color: var(--color-error-bg, #fee2e2); color: var(--color-error, #dc2626); }
.status--critical { background-color: var(--color-error-bg, #fee2e2); color: var(--color-error, #dc2626); }

.confidence {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.suggested-questions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.suggested-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.suggested-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.suggested-btn {
  font-size: var(--text-xs);
  white-space: nowrap;
}

.question-input {
  display: flex;
  gap: var(--spacing-2);
}

.question-input textarea {
  flex: 1;
  padding: var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-bg);
  color: var(--color-text);
  font-size: var(--text-sm);
  resize: none;
}

.question-input textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.submit-btn {
  align-self: flex-end;
  min-width: 80px;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-text-inverse);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  background-color: var(--color-error-bg, #fee2e2);
  color: var(--color-error, #dc2626);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.answer-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.answer-content {
  padding: var(--spacing-4);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-primary);
}

.answer-content p {
  margin: 0;
  line-height: var(--leading-relaxed);
}

.sources-section h4 {
  margin: 0 0 var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.source-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-2);
  background-color: var(--color-bg);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

.source-severity {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-weight: 600;
  text-transform: uppercase;
  flex-shrink: 0;
}

.severity--low { background-color: var(--color-success-bg, #dcfce7); color: var(--color-success, #16a34a); }
.severity--medium { background-color: var(--color-warning-bg, #fef3c7); color: var(--color-warning, #d97706); }
.severity--high { background-color: var(--color-error-bg, #fee2e2); color: var(--color-error, #dc2626); }
.severity--critical { background-color: var(--color-error-bg, #fee2e2); color: var(--color-error, #dc2626); }

.source-content {
  flex: 1;
  color: var(--color-text-secondary);
}

.source-date {
  flex-shrink: 0;
  color: var(--color-text-tertiary);
}
</style>