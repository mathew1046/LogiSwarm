<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  reportId: {
    type: String,
    required: true
  }
})

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const typing = ref(false)
const chatContainer = ref(null)

const suggestedQuestions = [
  'What were the main causes of this disruption?',
  'Which regions were most affected?',
  'What alternative routes were recommended?',
  'How could this disruption have been prevented?'
]

async function sendMessage(text = null) {
  const message = text || inputMessage.value.trim()
  if (!message || loading.value) return

  messages.value.push({
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })

  inputMessage.value = ''
  loading.value = true
  typing.value = true

  await scrollToBottom()

  try {
    const response = await fetch(`/api/reports/${props.reportId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    })

    const data = await response.json()

    if (data.error) {
      throw new Error(data.error)
    }

    typing.value = false
    messages.value.push({
      role: 'assistant',
      content: data.data?.response || 'I apologize, but I was unable to process that question.',
      timestamp: new Date().toISOString(),
      toolCalls: data.data?.tool_calls || []
    })
  } catch (err) {
    typing.value = false
    messages.value.push({
      role: 'assistant',
      content: `Error: ${err.message}`,
      timestamp: new Date().toISOString(),
      error: true
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

function formatTime(timestamp) {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  messages.value.push({
    role: 'assistant',
    content: 'Hello! I\'m the Report Agent. I can answer questions about this disruption report. What would you like to know?',
    timestamp: new Date().toISOString()
  })
})
</script>

<template>
  <div class="chat-interface">
    <div ref="chatContainer" class="chat-messages">
      <div 
        v-for="(message, index) in messages" 
        :key="index"
        :class="['chat-message', `chat-message--${message.role}`]"
      >
        <div class="message-avatar">
          <span v-if="message.role === 'user'">👤</span>
          <span v-else>🤖</span>
        </div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">{{ message.role === 'user' ? 'You' : 'Agent' }}</span>
            <span class="message-time">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="message-text" :class="{ error: message.error }">
            {{ message.content }}
          </div>
          <div v-if="message.toolCalls && message.toolCalls.length > 0" class="tool-calls">
            <details>
              <summary>Tool Calls ({{ message.toolCalls.length }})</summary>
              <div v-for="(call, i) in message.toolCalls" :key="i" class="tool-call">
                <strong>{{ call.tool }}</strong>
                <pre>{{ JSON.stringify(call.result, null, 2) }}</pre>
              </div>
            </details>
          </div>
        </div>
      </div>

      <div v-if="typing" class="chat-message chat-message--assistant">
        <div class="message-avatar">🤖</div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-role">Agent</span>
          </div>
          <div class="message-text typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="messages.length === 1" class="suggested-questions">
      <p class="suggestions-label">Suggested questions:</p>
      <button 
        v-for="question in suggestedQuestions" 
        :key="question"
        class="suggestion-btn"
        @click="sendMessage(question)"
      >
        {{ question }}
      </button>
    </div>

    <div class="chat-input">
      <input
        v-model="inputMessage"
        type="text"
        placeholder="Ask a question about this report..."
        :disabled="loading"
        @keyup.enter="sendMessage()"
      />
      <button 
        class="btn btn--primary" 
        @click="sendMessage()" 
        :disabled="loading || !inputMessage.trim()"
      >
        {{ loading ? '...' : 'Send' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 600px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-4);
}

.chat-message {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.chat-message--user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-full);
  flex-shrink: 0;
  font-size: var(--text-lg);
}

.message-content {
  max-width: 80%;
}

.message-header {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-1);
}

.message-role {
  font-weight: 600;
  font-size: var(--text-sm);
}

.message-time {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.message-text {
  padding: var(--spacing-3);
  border-radius: var(--radius-lg);
  background-color: var(--color-bg-secondary);
  line-height: var(--leading-relaxed);
}

.chat-message--user .message-text {
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
}

.message-text.error {
  background-color: rgba(239, 68, 68, 0.1);
  color: var(--color-error);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: var(--spacing-2);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background-color: var(--color-text-tertiary);
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.tool-calls {
  margin-top: var(--spacing-2);
}

.tool-calls summary {
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.tool-call {
  margin-top: var(--spacing-2);
  padding: var(--spacing-2);
  background-color: var(--color-bg);
  border-radius: var(--radius-sm);
}

.tool-call pre {
  margin: var(--spacing-1) 0 0;
  font-size: var(--text-xs);
  overflow-x: auto;
}

.suggested-questions {
  padding: 0 var(--spacing-4) var(--spacing-4);
}

.suggestions-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-2);
}

.suggestion-btn {
  display: block;
  width: 100%;
  padding: var(--spacing-2) var(--spacing-3);
  margin-bottom: var(--spacing-2);
  text-align: left;
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.suggestion-btn:hover {
  border-color: var(--color-primary);
  background-color: rgba(59, 130, 246, 0.05);
}

.chat-input {
  display: flex;
  gap: var(--spacing-2);
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border);
}

.chat-input input {
  flex: 1;
  padding: var(--spacing-2) var(--spacing-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
}

.chat-input input:focus {
  outline: none;
  border-color: var(--color-primary);
}
</style>