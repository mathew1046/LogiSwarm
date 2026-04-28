// LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
// Copyright (C) 2025 LogiSwarm Contributors
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'logiswarm_token'
const USER_KEY = 'logiswarm_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)
  const userEmail = computed(() => user.value?.email || '')
  const userRole = computed(() => user.value?.role || '')
  const isOperator = computed(() => ['operator', 'admin'].includes(user.value?.role))
  const isAdmin = computed(() => user.value?.role === 'admin')
  const displayName = computed(() => user.value?.display_name || user.value?.email || '')

  function getAuthHeaders() {
    if (!token.value) return {}
    return { Authorization: `Bearer ${token.value}` }
  }

  async function login(email, password) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      const envelope = await response.json()
      if (!response.ok || envelope.error) {
        throw new Error(envelope.error || envelope.detail || 'Login failed')
      }
      const data = envelope.data
      token.value = data.access_token
      user.value = data.user
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function register(email, password) {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      const envelope = await response.json()
      if (!response.ok || envelope.error) {
        throw new Error(envelope.error || envelope.detail || 'Registration failed')
      }
      // First user is auto-admin, auto-login after register
      const loginResult = await login(email, password)
      return loginResult
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return null
    try {
      const response = await fetch('/api/auth/me', {
        headers: { ...getAuthHeaders() }
      })
      if (!response.ok) {
        logout()
        return null
      }
      const envelope = await response.json()
      if (envelope.data) {
        user.value = envelope.data
        localStorage.setItem(USER_KEY, JSON.stringify(envelope.data))
      }
      return envelope.data
    } catch {
      return null
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return {
    token,
    user,
    loading,
    error,
    isAuthenticated,
    userEmail,
    userRole,
    isOperator,
    isAdmin,
    displayName,
    getAuthHeaders,
    login,
    register,
    logout,
    fetchCurrentUser
  }
})