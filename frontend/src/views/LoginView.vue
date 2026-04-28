<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeTab = ref('login')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const displayName = ref('')
const localError = ref(null)

const redirectTo = route.query.redirect || '/'

async function handleLogin() {
  localError.value = null
  const result = await authStore.login(email.value, password.value)
  if (result) {
    router.push(redirectTo)
  } else {
    localError.value = authStore.error || 'Login failed'
  }
}

async function handleRegister() {
  localError.value = null
  if (password.value !== confirmPassword.value) {
    localError.value = 'Passwords do not match'
    return
  }
  if (password.value.length < 8) {
    localError.value = 'Password must be at least 8 characters'
    return
  }
  const result = await authStore.register(email.value, password.value)
  if (result) {
    router.push(redirectTo)
  } else {
    localError.value = authStore.error || 'Registration failed'
  }
}
</script>

<template>
  <ProjectLayout>
    <div class="login-page">
      <div class="login-card card">
        <div class="login-header">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0110 0v4"/>
          </svg>
          <h1>{{ activeTab === 'login' ? 'Sign In' : 'Create Account' }}</h1>
        </div>

        <div class="tab-bar">
          <button :class="['tab-btn', { active: activeTab === 'login' }]" @click="activeTab = 'login'; localError = null">Login</button>
          <button :class="['tab-btn', { active: activeTab === 'register' }]" @click="activeTab = 'register'; localError = null">Register</button>
        </div>

        <div v-if="localError || authStore.error" class="error-banner">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          {{ localError || authStore.error }}
        </div>

        <form v-if="activeTab === 'login'" @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label class="label">Email</label>
            <input v-model="email" type="email" class="input" placeholder="you@example.com" required autocomplete="email" />
          </div>
          <div class="form-group">
            <label class="label">Password</label>
            <input v-model="password" type="password" class="input" placeholder="••••••••" required autocomplete="current-password" />
          </div>
          <button type="submit" class="btn btn--primary btn--lg btn--full" :disabled="authStore.loading">
            <svg v-if="authStore.loading" class="btn-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ authStore.loading ? 'Signing in...' : 'Sign In' }}
          </button>
        </form>

        <form v-else @submit.prevent="handleRegister" class="login-form">
          <div class="form-group">
            <label class="label">Email</label>
            <input v-model="email" type="email" class="input" placeholder="you@example.com" required autocomplete="email" />
          </div>
          <div class="form-group">
            <label class="label">Display Name (optional)</label>
            <input v-model="displayName" type="text" class="input" placeholder="Your name" autocomplete="name" />
          </div>
          <div class="form-group">
            <label class="label">Password</label>
            <input v-model="password" type="password" class="input" placeholder="Minimum 8 characters" required autocomplete="new-password" minlength="8" />
          </div>
          <div class="form-group">
            <label class="label">Confirm Password</label>
            <input v-model="confirmPassword" type="password" class="input" placeholder="••••••••" required autocomplete="new-password" />
          </div>
          <button type="submit" class="btn btn--primary btn--lg btn--full" :disabled="authStore.loading">
            <svg v-if="authStore.loading" class="btn-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
            </svg>
            {{ authStore.loading ? 'Creating account...' : 'Create Account' }}
          </button>
        </form>

        <p class="login-hint">
          {{ activeTab === 'login' ? "Don't have an account?" : 'Already have an account?' }}
          <button class="link-btn" @click="activeTab = activeTab === 'login' ? 'register' : 'login'; localError = null">
            {{ activeTab === 'login' ? 'Register' : 'Sign in' }}
          </button>
        </p>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.login-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.login-card {
  max-width: 420px;
  width: 100%;
  margin: 0 auto;
}

.login-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-6);
}

.login-header h1 {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.tab-bar {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-6);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing-2);
}

.tab-btn {
  flex: 1;
  padding: var(--spacing-2) var(--spacing-4);
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-text);
  background: var(--color-bg-tertiary);
}

.tab-btn.active {
  color: var(--color-primary);
  border-bottom: 2px solid var(--color-primary);
}

.error-banner {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-critical-bg);
  color: var(--color-critical);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-4);
  font-size: var(--text-sm);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.btn--full {
  width: 100%;
  margin-top: var(--spacing-2);
}

.btn-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-hint {
  text-align: center;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-4);
}

.link-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: 500;
  padding: 0;
}

.link-btn:hover {
  text-decoration: underline;
}
</style>