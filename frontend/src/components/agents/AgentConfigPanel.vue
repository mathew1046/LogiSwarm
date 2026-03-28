<!--
LogiSwarm - Geo-Aware Swarm Intelligence for Supply Chains
Copyright (C) 2025 LogiSwarm Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAgentStore } from '@/stores/agent'

const agentStore = useAgentStore()
const selectedRegion = ref(null)
const loading = ref(false)
const saving = ref(false)
const config = ref({})

const agents = computed(() => agentStore.agents)

const defaultConfig = {
  poll_interval_seconds: 60,
  confidence_threshold: 0.75,
  auto_act_enabled: true,
  broadcast_to_neighbors: true
}

const regions = computed(() => 
  agents.value.map(a => ({
    id: a.region_id,
    name: a.region_name,
    running: a.running
  }))
)

async function loadConfig(regionId) {
  loading.value = true
  try {
    const result = await agentStore.fetchAgentConfig(regionId)
    config.value = result || { ...defaultConfig }
    selectedRegion.value = regionId
  } catch (err) {
    console.error('Failed to load config:', err)
    config.value = { ...defaultConfig }
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  if (!selectedRegion.value) return
  saving.value = true
  try {
    await agentStore.updateAgentConfig(selectedRegion.value, config.value)
  } catch (err) {
    console.error('Failed to save config:', err)
  } finally {
    saving.value = false
  }
}

function resetToDefaults() {
  config.value = { ...defaultConfig }
}

function getPreviewText() {
  const threshold = config.value.confidence_threshold || 0.75
  const messages = []
  if (threshold >= 0.9) {
    messages.push('Very few signals will trigger auto-action (strict)')
  } else if (threshold >= 0.75) {
    messages.push('Only high-confidence signals will trigger auto-action')
  } else if (threshold >= 0.6) {
    messages.push('Moderate signals will trigger auto-action')
  } else {
    messages.push('Most signals will trigger auto-action (permissive)')
  }
  
  if (config.value.auto_act_enabled) {
    messages.push('Auto-action is ENABLED')
  } else {
    messages.push('Auto-action is DISABLED (recommendations only)')
  }
  
  if (config.value.broadcast_to_neighbors) {
    messages.push('Neighbors will be notified of alerts')
  } else {
    messages.push('Neighbors will NOT be notified')
  }
  
  return messages
}

onMounted(async () => {
  await agentStore.fetchAgents()
  if (regions.value.length > 0) {
    await loadConfig(regions.value[0].id)
  }
})
</script>

<template>
  <div class="config-panel">
    <div class="panel-header">
      <h2>Agent Configuration</h2>
      <p class="text-secondary">Tune agent parameters for each monitoring region.</p>
    </div>

    <div class="config-layout">
      <div class="regions-list">
        <h3>Regions</h3>
        <div class="regions-list-content">
          <button
            v-for="region in regions"
            :key="region.id"
            :class="['region-btn', { active: selectedRegion === region.id }]"
            @click="loadConfig(region.id)"
          >
            <span class="region-name">{{ region.name }}</span>
            <span :class="['status-indicator', { running: region.running }]">
              {{ region.running ? '●' : '○' }}
            </span>
          </button>
        </div>
      </div>

      <div class="config-form">
        <div v-if="loading" class="loading">
          <div class="loading__spinner"></div>
        </div>

        <template v-else-if="selectedRegion">
          <h3>{{ regions.find(r => r.id === selectedRegion)?.name }}</h3>

          <div class="form-section">
            <label class="form-label">
              Poll Interval: {{ config.poll_interval_seconds || 60 }} seconds
            </label>
            <input
              v-model.number="config.poll_interval_seconds"
              type="range"
              min="30"
              max="300"
              step="10"
              class="slider"
            />
            <div class="slider-labels">
              <span>30s</span>
              <span>300s</span>
            </div>
          </div>

          <div class="form-section">
            <label class="form-label">
              Confidence Threshold: {{ ((config.confidence_threshold || 0.75) * 100).toFixed(0) }}%
            </label>
            <input
              v-model.number="config.confidence_threshold"
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              class="slider"
            />
            <div class="slider-labels">
              <span>50%</span>
              <span>95%</span>
            </div>
          </div>

          <div class="form-section">
            <div class="toggle-row">
              <label class="toggle-label">
                <span class="label-text">Auto-Act Enabled</span>
                <span class="label-desc">Automatically execute high-confidence recommendations</span>
              </label>
              <label class="toggle">
                <input type="checkbox" v-model="config.auto_act_enabled" />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="form-section">
            <div class="toggle-row">
              <label class="toggle-label">
                <span class="label-text">Broadcast to Neighbors</span>
                <span class="label-desc">Alert neighboring regions when risk is detected</span>
              </label>
              <label class="toggle">
                <input type="checkbox" v-model="config.broadcast_to_neighbors" />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>

          <div class="config-preview">
            <h4>Live Preview</h4>
            <ul>
              <li v-for="(msg, i) in getPreviewText()" :key="i">{{ msg }}</li>
            </ul>
          </div>

          <div class="form-actions">
            <button class="btn btn--secondary" @click="resetToDefaults">Reset to Defaults</button>
            <button class="btn btn--primary" @click="saveConfig" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save Configuration' }}
            </button>
          </div>
        </template>

        <div v-else class="empty-state">
          <p>Select a region to configure</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  margin-bottom: var(--spacing-6);
}

.panel-header h2 {
  margin-bottom: var(--spacing-1);
}

.text-secondary {
  color: var(--color-text-secondary);
}

.config-layout {
  display: grid;
  grid-template-columns: 250px 1fr;
  gap: var(--spacing-6);
  flex: 1;
}

.regions-list h3 {
  margin-bottom: var(--spacing-3);
}

.regions-list-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.region-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  width: 100%;
  text-align: left;
}

.region-btn:hover {
  border-color: var(--color-primary);
}

.region-btn.active {
  border-color: var(--color-primary);
  background-color: rgba(59, 130, 246, 0.1);
}

.region-name {
  font-weight: 500;
}

.status-indicator {
  font-size: var(--text-lg);
  color: var(--color-text-tertiary);
}

.status-indicator.running {
  color: var(--color-success);
}

.config-form h3 {
  margin-bottom: var(--spacing-4);
}

.form-section {
  margin-bottom: var(--spacing-6);
}

.form-label {
  display: block;
  font-weight: 500;
  margin-bottom: var(--spacing-2);
}

.slider {
  width: 100%;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-border);
  border-radius: var(--radius-full);
  outline: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-top: var(--spacing-1);
}

.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toggle-label {
  flex: 1;
}

.label-text {
  display: block;
  font-weight: 500;
}

.label-desc {
  display: block;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.toggle {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-border);
  border-radius: var(--radius-full);
  transition: var(--transition-fast);
}

.toggle-slider::before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: var(--radius-full);
  transition: var(--transition-fast);
}

.toggle input:checked + .toggle-slider {
  background-color: var(--color-primary);
}

.toggle input:checked + .toggle-slider::before {
  transform: translateX(24px);
}

.config-preview {
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.config-preview h4 {
  margin-bottom: var(--spacing-2);
}

.config-preview ul {
  margin: 0;
  padding-left: var(--spacing-4);
}

.config-preview li {
  margin-bottom: var(--spacing-1);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.form-actions {
  display: flex;
  gap: var(--spacing-3);
}
</style>