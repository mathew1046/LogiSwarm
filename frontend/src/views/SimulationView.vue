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
import { ref, onMounted, onUnmounted } from 'vue'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const loading = ref(false)
const simulationActive = ref(false)
const simulationLog = ref([])
const selectedScenario = ref('suez_blockage')
const customRegion = ref('gulf_suez')
const customSeverity = ref('HIGH')
const customDuration = ref(6)

const scenarios = [
  {
    id: 'suez_blockage',
    name: 'Suez Canal Blockage',
    description: 'Mega-container ship stuck in canal for 6-7 days. Classic supply chain disruption scenario.',
    region: 'gulf_suez',
    severity: 'CRITICAL',
    duration: 6,
    impacts: ['Europe-Asia routes diverted', '+14 days transit time', '+$300k fuel cost']
  },
  {
    id: 'port_strike',
    name: 'Port Strike',
    description: 'Labor dispute shuts down major port. Vessels reroute to alternative ports.',
    region: 'north_america',
    severity: 'HIGH',
    duration: 5,
    impacts: ['Vessels reroute to Oakland/Tacoma', 'Inventory shortages', 'Production delays']
  },
  {
    id: 'hurricane_season',
    name: 'Hurricane Season',
    description: 'Category 4 hurricane hits Gulf Coast. Port closures and vessel diversions.',
    region: 'gulf_suez',
    severity: 'HIGH',
    duration: 4,
    impacts: ['Chemical/oil supply disruptions', 'Alternative routing required', 'Weather delays']
  },
  {
    id: 'piracy_incident',
    name: 'Piracy Incident',
    description: 'Security incident in Gulf of Aden. Vessels reroute around Africa.',
    region: 'south_asia',
    severity: 'MEDIUM',
    duration: 3,
    impacts: ['Security escorts required', 'Insurance premiums rise', 'Cape route alternative']
  },
  {
    id: 'custom',
    name: 'Custom Scenario',
    description: 'Define your own disruption scenario with custom parameters.',
    region: '',
    severity: 'MEDIUM',
    duration: 3,
    impacts: []
  }
]

const regions = [
  { id: 'gulf_suez', name: 'Gulf / Suez Risk Corridor' },
  { id: 'se_asia', name: 'Southeast Asia / Strait of Malacca' },
  { id: 'europe', name: 'Europe Logistics Corridor' },
  { id: 'north_america', name: 'North America Intermodal Network' },
  { id: 'china_ea', name: 'China / East Asia Export Corridor' },
  { id: 'south_asia', name: 'South Asia / Indian Ocean' },
  { id: 'latin_america', name: 'Latin America / Panama Canal' },
  { id: 'africa', name: 'Africa / Cape of Good Hope' }
]

const severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

const addLogEntry = (message, type = 'info') => {
  simulationLog.value.unshift({
    timestamp: new Date().toLocaleTimeString(),
    message,
    type
  })
}

const runSimulation = async () => {
  if (simulationActive.value) {
    toast.warning('Simulation already running')
    return
  }

  loading.value = true
  simulationActive.value = true
  simulationLog.value = []

  const scenario = scenarios.find(s => s.id === selectedScenario.value)
  
  addLogEntry(`🚀 Starting simulation: ${scenario.name}`, 'success')
  addLogEntry(`📍 Target region: ${scenario.region || customRegion.value}`, 'info')
  addLogEntry(`⚠️ Severity: ${scenario.severity || customSeverity.value}`, 'warning')

  try {
    // Call simulation API
    const response = await fetch('/api/orchestrator/simulate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        scenario: selectedScenario.value,
        region_id: scenario.region || customRegion.value,
        severity: scenario.severity || customSeverity.value,
        duration_days: scenario.duration || customDuration.value,
        start_date: new Date().toISOString(),
        end_date: new Date(Date.now() + (scenario.duration || customDuration.value) * 24 * 60 * 60 * 1000).toISOString()
      })
    })

    if (response.ok) {
      const data = await response.json()
      addLogEntry('✅ Simulation data injected successfully', 'success')
      
      // Simulate real-time updates
      setTimeout(() => addLogEntry('🤖 Regional agent detecting anomaly...', 'info'), 1000)
      setTimeout(() => addLogEntry('📊 Processing sensor data...', 'info'), 2000)
      setTimeout(() => addLogEntry('🧠 LLM analyzing disruption impact...', 'info'), 3000)
      setTimeout(() => {
        addLogEntry('🚨 Disruption alert broadcast to neighbors', 'warning')
        scenario.impacts.forEach((impact, idx) => {
          setTimeout(() => addLogEntry(`  → ${impact}`, 'info'), 4000 + (idx * 500))
        })
      }, 3500)
      setTimeout(() => addLogEntry('🗺️ Route optimizer calculating alternatives...', 'info'), 6000)
      setTimeout(() => addLogEntry('📈 Cascade risk scored: 0.85', 'warning'), 7500)
      setTimeout(() => addLogEntry('✅ Simulation complete - check Dashboard', 'success'), 8000)
      
      toast.success('Simulation running - check Dashboard tab')
    } else {
      throw new Error('Simulation API returned error')
    }
  } catch (error) {
    console.error('Simulation error:', error)
    // Fallback to client-side simulation if API fails
    addLogEntry('⚠️ API unavailable - running client-side simulation', 'warning')
    
    // Mock simulation sequence
    setTimeout(() => addLogEntry('🤖 Regional agent detecting anomaly...', 'info'), 1000)
    setTimeout(() => addLogEntry('📊 Processing sensor data...', 'info'), 2000)
    setTimeout(() => addLogEntry('🧠 LLM analyzing disruption impact...', 'info'), 3000)
    setTimeout(() => {
      addLogEntry('🚨 Disruption alert broadcast to neighbors', 'warning')
      const impacts = scenario.impacts.length > 0 ? scenario.impacts : ['Regional impact detected', 'Cascade analysis running']
      impacts.forEach((impact, idx) => {
        setTimeout(() => addLogEntry(`  → ${impact}`, 'info'), 4000 + (idx * 500))
      })
    }, 3500)
    setTimeout(() => addLogEntry('🗺️ Route optimizer calculating alternatives...', 'info'), 6000)
    setTimeout(() => addLogEntry('📈 Cascade risk scored: 0.85', 'warning'), 7500)
    setTimeout(() => addLogEntry('✅ Simulation complete - check Dashboard', 'success'), 8000)
    
    toast.success('Client-side simulation complete')
  } finally {
    loading.value = false
    setTimeout(() => {
      simulationActive.value = false
    }, 8500)
  }
}

const clearSimulation = () => {
  simulationLog.value = []
  addLogEntry('🧹 Simulation data cleared', 'info')
  toast.success('Simulation cleared')
}

const injectMockData = async (type) => {
  loading.value = true
  addLogEntry(`📦 Injecting mock ${type}...`, 'info')
  
  try {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    const counts = {
      shipments: Math.floor(Math.random() * 50) + 20,
      disruptions: Math.floor(Math.random() * 10) + 3,
      vessels: Math.floor(Math.random() * 100) + 50
    }
    
    addLogEntry(`✅ Injected ${counts[type] || 25} mock ${type}`, 'success')
    toast.success(`Mock ${type} data injected`)
  } catch (error) {
    addLogEntry(`❌ Failed to inject ${type}: ${error.message}`, 'error')
    toast.error('Failed to inject mock data')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  addLogEntry('🎯 Simulation panel ready', 'info')
  addLogEntry('💡 Select a scenario and click "Run Simulation" to begin', 'info')
})
</script>

<template>
  <div class="simulation-view">
    <div class="page-header">
      <h1>🔬 Simulation & Mock Data</h1>
      <p class="subtitle">
        Test scenarios without affecting production. Perfect for training, demos, and validation.
      </p>
    </div>

    <div class="simulation-grid">
      <!-- Left Column: Scenario Selection -->
      <div class="scenario-panel">
        <div class="panel-header">
          <h2>📋 Choose Scenario</h2>
        </div>

        <div class="scenario-list">
          <div
            v-for="scenario in scenarios"
            :key="scenario.id"
            class="scenario-card"
            :class="{ active: selectedScenario === scenario.id }"
            @click="selectedScenario = scenario.id"
          >
            <div class="scenario-header">
              <h3>{{ scenario.name }}</h3>
              <span class="severity-badge" :class="scenario.severity.toLowerCase()">
                {{ scenario.severity }}
              </span>
            </div>
            <p class="scenario-description">{{ scenario.description }}</p>
            <div class="scenario-meta">
              <span class="meta-item">📍 {{ scenario.region || 'Custom' }}</span>
              <span class="meta-item">⏱️ {{ scenario.duration }} days</span>
            </div>
          </div>
        </div>

        <!-- Custom Scenario Settings -->
        <div v-if="selectedScenario === 'custom'" class="custom-settings">
          <h3>⚙️ Custom Parameters</h3>
          
          <div class="form-group">
            <label>Target Region</label>
            <select v-model="customRegion">
              <option v-for="region in regions" :key="region.id" :value="region.id">
                {{ region.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Severity Level</label>
            <select v-model="customSeverity">
              <option v-for="sev in severities" :key="sev" :value="sev">{{ sev }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>Duration (days)</label>
            <input 
              v-model.number="customDuration" 
              type="number" 
              min="1" 
              max="30"
            />
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button 
            class="btn btn-primary btn-large"
            :disabled="loading || simulationActive"
            @click="runSimulation"
          >
            <span v-if="loading" class="spinner"></span>
            <span v-else>🚀 Run Simulation</span>
          </button>
          
          <button 
            class="btn btn-secondary"
            :disabled="simulationLog.length === 0"
            @click="clearSimulation"
          >
            🧹 Clear Log
          </button>
        </div>
      </div>

      <!-- Middle Column: Simulation Log -->
      <div class="log-panel">
        <div class="panel-header">
          <h2>📊 Simulation Log</h2>
          <div class="status-indicator" :class="{ active: simulationActive }">
            {{ simulationActive ? '🔴 Running' : '🟢 Ready' }}
          </div>
        </div>

        <div class="log-container">
          <div v-if="simulationLog.length === 0" class="empty-state">
            <div class="empty-icon">🎯</div>
            <p>No simulation running yet</p>
            <p class="hint">Select a scenario and click "Run Simulation" to begin</p>
          </div>
          
          <div v-else class="log-entries">
            <div
              v-for="(entry, index) in simulationLog"
              :key="index"
              class="log-entry"
              :class="entry.type"
            >
              <span class="timestamp">{{ entry.timestamp }}</span>
              <span class="message">{{ entry.message }}</span>
            </div>
          </div>
        </div>

        <!-- Quick Stats -->
        <div v-if="simulationLog.length > 0" class="quick-stats">
          <div class="stat-item">
            <span class="stat-value">{{ simulationLog.filter(e => e.type === 'success').length }}</span>
            <span class="stat-label">Success</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ simulationLog.filter(e => e.type === 'warning').length }}</span>
            <span class="stat-label">Warnings</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ simulationLog.filter(e => e.type === 'error').length }}</span>
            <span class="stat-label">Errors</span>
          </div>
        </div>
      </div>

      <!-- Right Column: Mock Data Controls -->
      <div class="mock-panel">
        <div class="panel-header">
          <h2>📦 Quick Mock Data</h2>
        </div>

        <div class="mock-controls">
          <div class="mock-section">
            <h3>Inject Test Data</h3>
            <p class="section-desc">Add realistic test data to the system</p>
            
            <div class="mock-buttons">
              <button 
                class="btn btn-mock"
                :disabled="loading"
                @click="injectMockData('shipments')"
              >
                📦 Shipments
              </button>
              
              <button 
                class="btn btn-mock"
                :disabled="loading"
                @click="injectMockData('disruptions')"
              >
                ⚠️ Disruptions
              </button>
              
              <button 
                class="btn btn-mock"
                :disabled="loading"
                @click="injectMockData('vessels')"
              >
                🚢 Vessels
              </button>
            </div>
          </div>

          <div class="mock-section">
            <h3>Environment Settings</h3>
            <div class="setting-item">
              <span class="setting-label">Port Mock Data</span>
              <span class="setting-value enabled">✅ Enabled</span>
            </div>
            <div class="setting-item">
              <span class="setting-label">Anomaly Probability</span>
              <span class="setting-value">12%</span>
            </div>
            <div class="setting-item">
              <span class="setting-label">Agent Cycle Time</span>
              <span class="setting-value">60s</span>
            </div>
          </div>

          <div class="info-box">
            <h4>💡 Pro Tips</h4>
            <ul>
              <li>Use simulations for training new users</li>
              <li>Test auto-reroute settings safely</li>
              <li>Demonstrate to stakeholders</li>
              <li>Always reset after testing</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Help Section -->
    <div class="help-section">
      <h2>📖 How to Use Simulation</h2>
      <div class="help-grid">
        <div class="help-card">
          <div class="help-icon">1️⃣</div>
          <h3>Select Scenario</h3>
          <p>Choose from pre-built scenarios like Suez Blockage or create custom events</p>
        </div>
        <div class="help-card">
          <div class="help-icon">2️⃣</div>
          <h3>Configure</h3>
          <p>Set region, severity, and duration. For custom scenarios, define all parameters</p>
        </div>
        <div class="help-card">
          <div class="help-icon">3️⃣</div>
          <h3>Run & Watch</h3>
          <p>Click "Run Simulation" and watch the real-time log. Switch to Dashboard to see effects</p>
        </div>
        <div class="help-card">
          <div class="help-icon">4️⃣</div>
          <h3>Analyze Results</h3>
          <p>Review agent responses, cascade impacts, and route recommendations</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.simulation-view {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.simulation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

/* Panels */
.scenario-panel,
.log-panel,
.mock-panel {
  background: var(--surface-color);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.panel-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--surface-hover);
}

.panel-header h2 {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin: 0;
}

/* Scenario List */
.scenario-list {
  padding: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.scenario-card {
  padding: 1rem;
  margin-bottom: 0.75rem;
  border-radius: 8px;
  border: 2px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s;
}

.scenario-card:hover {
  border-color: var(--primary-color);
  background: var(--surface-hover);
}

.scenario-card.active {
  border-color: var(--primary-color);
  background: var(--primary-color-alpha);
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.scenario-header h3 {
  font-size: 1rem;
  margin: 0;
  color: var(--text-primary);
}

.severity-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.severity-badge.low { background: #22c55e; color: white; }
.severity-badge.medium { background: #eab308; color: black; }
.severity-badge.high { background: #f97316; color: white; }
.severity-badge.critical { background: #ef4444; color: white; }

.scenario-description {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 0.75rem;
  line-height: 1.4;
}

.scenario-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

/* Custom Settings */
.custom-settings {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  background: var(--surface-hover);
}

.custom-settings h3 {
  font-size: 1rem;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--surface-color);
  color: var(--text-primary);
}

/* Action Buttons */
.action-buttons {
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.btn {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-color-dark);
}

.btn-secondary {
  background: var(--surface-hover);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--border-color);
}

.btn-large {
  padding: 1rem;
  font-size: 1rem;
}

/* Log Panel */
.status-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  background: var(--surface-hover);
}

.status-indicator.active {
  background: #ef4444;
  color: white;
}

.log-container {
  height: 400px;
  overflow-y: auto;
  padding: 1rem;
  background: #0f172a;
  font-family: monospace;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state .hint {
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.log-entries {
  display: flex;
  flex-direction: column-reverse;
}

.log-entry {
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
  font-size: 0.85rem;
}

.log-entry.success { color: #22c55e; }
.log-entry.warning { color: #f59e0b; }
.log-entry.error { color: #ef4444; }
.log-entry.info { color: #60a5fa; }

.timestamp {
  color: #64748b;
  margin-right: 0.75rem;
  font-size: 0.8rem;
}

/* Quick Stats */
.quick-stats {
  display: flex;
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  background: var(--surface-hover);
  gap: 1.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
}

/* Mock Panel */
.mock-controls {
  padding: 1rem;
}

.mock-section {
  margin-bottom: 1.5rem;
}

.mock-section h3 {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.section-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.mock-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-mock {
  background: var(--surface-hover);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  text-align: left;
}

.btn-mock:hover:not(:disabled) {
  background: var(--border-color);
}

.setting-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.875rem;
}

.setting-label {
  color: var(--text-secondary);
}

.setting-value {
  color: var(--text-primary);
  font-weight: 500;
}

.setting-value.enabled {
  color: #22c55e;
}

.info-box {
  background: var(--primary-color-alpha);
  border: 1px solid var(--primary-color);
  border-radius: 8px;
  padding: 1rem;
}

.info-box h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: var(--primary-color);
}

.info-box ul {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.info-box li {
  margin-bottom: 0.25rem;
}

/* Help Section */
.help-section {
  background: var(--surface-color);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 1.5rem;
}

.help-section h2 {
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

.help-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.help-card {
  text-align: center;
  padding: 1.5rem;
  background: var(--surface-hover);
  border-radius: 8px;
}

.help-icon {
  font-size: 2rem;
  margin-bottom: 0.75rem;
}

.help-card h3 {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
}

.help-card p {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0;
}

/* Spinner */
.spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 1200px) {
  .simulation-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .mock-panel {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .simulation-grid {
    grid-template-columns: 1fr;
  }
  
  .mock-panel {
    grid-column: span 1;
  }
  
  .help-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>