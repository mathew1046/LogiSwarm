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

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'

const router = useRouter()
const projectStore = useProjectStore()

const step = ref(1)
const projectName = ref('')
const selectedRegions = ref([])
const thresholds = ref({})
const shipments = ref([])
const loading = ref(false)

const regions = [
  { id: 'se_asia', name: 'SE Asia', description: 'Malacca Strait, Singapore hub', bbox: '95°E-140°E, 10°S-25°N' },
  { id: 'europe', name: 'Europe', description: 'Rotterdam-Hamburg-Antwerp corridor', bbox: '0°E-25°E, 45°N-60°N' },
  { id: 'gulf_suez', name: 'Gulf/Suez', description: 'Suez Canal, Persian Gulf', bbox: '30°E-60°E, 20°N-32°N' },
  { id: 'north_america', name: 'North America', description: 'US West Coast, Panama', bbox: '130°W-70°W, 25°N-50°N' },
  { id: 'china_ea', name: 'China/East Asia', description: 'Shanghai-Ningbo-Busan cluster', bbox: '110°E-145°E, 20°N-45°N' }
]

const steps = [
  { id: 1, title: 'Name & Regions', description: 'Name your project and select monitoring regions' },
  { id: 2, title: 'Thresholds', description: 'Configure confidence thresholds per region' },
  { id: 3, title: 'Shipments', description: 'Add shipments to track' },
  { id: 4, title: 'Review', description: 'Review and launch' }
]

const canProceed = computed(() => {
  if (step.value === 1) {
    return projectName.value.trim().length > 0 && selectedRegions.value.length > 0
  }
  if (step.value === 2) {
    return selectedRegions.value.every(r => thresholds.value[r] !== undefined)
  }
  if (step.value === 3) {
    return true // Shipments are optional
  }
  return true
})

function toggleRegion(regionId) {
  const index = selectedRegions.value.indexOf(regionId)
  if (index === -1) {
    selectedRegions.value.push(regionId)
    thresholds.value[regionId] = 0.75
  } else {
    selectedRegions.value.splice(index, 1)
    delete thresholds.value[regionId]
  }
}

function addShipment() {
  shipments.value.push({
    id: Date.now(),
    shipment_ref: '',
    carrier: '',
    origin: '',
    destination: '',
    route: []
  })
}

function removeShipment(index) {
  shipments.value.splice(index, 1)
}

async function submitProject() {
  loading.value = true
  try {
    const project = await projectStore.createProject({
      name: projectName.value,
      config: {
        regions: selectedRegions.value,
        thresholds: thresholds.value,
        shipments: shipments.value.filter(s => s.shipment_ref && s.origin && s.destination)
      }
    })
    if (project) {
      router.push(`/projects/${project.id}`)
    }
  } catch (err) {
    console.error('Failed to create project:', err)
  } finally {
    loading.value = false
  }
}

function prevStep() {
  if (step.value > 1) {
    step.value--
  }
}

function nextStep() {
  if (step.value < 4) {
    step.value++
  }
}
</script>

<template>
  <ProjectLayout>
    <div class="project-create">
      <h1>Create New Project</h1>
      
      <!-- Step Indicator -->
      <div class="step-indicator">
        <div 
          v-for="s in steps" 
          :key="s.id" 
          :class="['step-item', { active: step === s.id, completed: step > s.id }]"
        >
          <div class="step-number">{{ step > s.id ? '✓' : s.id }}</div>
          <div class="step-info">
            <div class="step-title">{{ s.title }}</div>
            <div class="step-description">{{ s.description }}</div>
          </div>
        </div>
      </div>

      <!-- Step 1: Name & Regions -->
      <div v-if="step === 1" class="card step-content">
        <h2>Step 1: Name Your Project</h2>
        <p class="step-subtitle">Give your project a name and select which regions to monitor.</p>
        
        <div class="form-group">
          <label class="label">Project Name *</label>
          <input 
            v-model="projectName" 
            type="text" 
            class="input" 
            placeholder="e.g., APAC Supply Chain Monitor"
            maxlength="255"
          />
        </div>

        <h3 class="mt-6">Select Monitoring Regions *</h3>
        <p class="text-secondary mb-4">Choose at least one region for your agents to monitor.</p>
        
        <div class="regions-grid">
          <div 
            v-for="region in regions" 
            :key="region.id"
            :class="['region-card', { selected: selectedRegions.includes(region.id) }]"
            @click="toggleRegion(region.id)"
          >
            <div class="region-header">
              <h4>{{ region.name }}</h4>
              <div :class="['region-checkbox', { checked: selectedRegions.includes(region.id) }]">
                <svg v-if="selectedRegions.includes(region.id)" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                  <path d="M20 6L9 17l-5-5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <p class="region-description">{{ region.description }}</p>
            <p class="region-bbox">{{ region.bbox }}</p>
          </div>
        </div>
      </div>

      <!-- Step 2: Thresholds -->
      <div v-else-if="step === 2" class="card step-content">
        <h2>Step 2: Configure Thresholds</h2>
        <p class="step-subtitle">Set confidence thresholds for each region. Higher values mean fewer but more certain alerts.</p>
        
        <div class="thresholds-list">
          <div v-for="regionId in selectedRegions" :key="regionId" class="threshold-item">
            <div class="threshold-header">
              <h4>{{ regions.find(r => r.id === regionId)?.name }}</h4>
              <span class="threshold-value">{{ (thresholds[regionId] || 0.75).toFixed(2) }}</span>
            </div>
            <input 
              v-model.number="thresholds[regionId]"
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              class="threshold-slider"
            />
            <div class="threshold-labels">
              <span>More Alerts (0.50)</span>
              <span>Fewer Alerts (0.95)</span>
            </div>
            <p class="threshold-preview">
              At this threshold, alerts will trigger when agent confidence is at least 
              {{ ((thresholds[regionId] || 0.75) * 100).toFixed(0) }}%.
            </p>
          </div>
        </div>
      </div>

      <!-- Step 3: Shipments -->
      <div v-else-if="step === 3" class="card step-content">
        <h2>Step 3: Add Shipments</h2>
        <p class="step-subtitle">Optionally add shipments to track through this project. You can add more later.</p>
        
        <button class="btn btn--secondary" @click="addShipment">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 4v16m8-8H4" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Add Shipment
        </button>

        <div v-if="shipments.length === 0" class="empty-state mt-6">
          <p class="text-secondary">No shipments added yet. This step is optional.</p>
        </div>

        <div v-else class="shipments-list mt-6">
          <div v-for="(shipment, index) in shipments" :key="shipment.id" class="shipment-item">
            <div class="shipment-header">
              <h4>Shipment {{ index + 1 }}</h4>
              <button class="btn btn--danger btn--sm" @click="removeShipment(index)">Remove</button>
            </div>
            <div class="grid grid--2">
              <div class="form-group">
                <label class="label">Shipment Reference</label>
                <input v-model="shipment.shipment_ref" type="text" class="input" placeholder="e.g., SHIP-001" />
              </div>
              <div class="form-group">
                <label class="label">Carrier</label>
                <input v-model="shipment.carrier" type="text" class="input" placeholder="e.g., Maersk" />
              </div>
              <div class="form-group">
                <label class="label">Origin</label>
                <input v-model="shipment.origin" type="text" class="input" placeholder="e.g., Shanghai" />
              </div>
              <div class="form-group">
                <label class="label">Destination</label>
                <input v-model="shipment.destination" type="text" class="input" placeholder="e.g., Rotterdam" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4: Review -->
      <div v-else-if="step === 4" class="card step-content">
        <h2>Step 4: Review & Launch</h2>
        <p class="step-subtitle">Review your project configuration before creating.</p>
        
        <div class="review-section">
          <h3>Project Name</h3>
          <p class="review-value">{{ projectName }}</p>
        </div>

        <div class="review-section">
          <h3>Monitoring Regions ({{ selectedRegions.length }})</h3>
          <div class="review-regions">
            <span v-for="regionId in selectedRegions" :key="regionId" class="badge badge--low">
              {{ regions.find(r => r.id === regionId)?.name }}
            </span>
          </div>
        </div>

        <div class="review-section">
          <h3>Thresholds</h3>
          <div class="review-thresholds">
            <div v-for="regionId in selectedRegions" :key="regionId" class="threshold-summary">
              <span>{{ regions.find(r => r.id === regionId)?.name }}</span>
              <span class="threshold-value">{{ (thresholds[regionId] || 0.75).toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <div v-if="shipments.filter(s => s.shipment_ref).length > 0" class="review-section">
          <h3>Shipments ({{ shipments.filter(s => s.shipment_ref).length }})</h3>
          <ul class="review-shipments">
            <li v-for="(shipment, index) in shipments.filter(s => s.shipment_ref)" :key="shipment.id">
              {{ shipment.shipment_ref }}: {{ shipment.origin }} → {{ shipment.destination }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Navigation Buttons -->
      <div class="step-actions">
        <button v-if="step > 1" class="btn btn--secondary" @click="prevStep">
          Previous
        </button>
        <button v-if="step < 4" class="btn btn--primary" @click="nextStep" :disabled="!canProceed">
          Next
        </button>
        <button v-if="step === 4" class="btn btn--primary btn--lg" @click="submitProject" :disabled="loading">
          {{ loading ? 'Creating...' : 'Create Project' }}
        </button>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.project-create {
  max-width: 900px;
  margin: 0 auto;
}

.step-indicator {
  display: flex;
  margin-bottom: var(--spacing-8);
  gap: var(--spacing-2);
}

.step-item {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-radius: var(--radius-lg);
  background-color: var(--color-bg-secondary);
  transition: all var(--transition-normal);
}

.step-item.active {
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
}

.step-item.completed {
  background-color: var(--color-success);
  color: var(--color-text-inverse);
}

.step-number {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background-color: var(--color-bg-tertiary);
  font-weight: 600;
  flex-shrink: 0;
}

.step-item.active .step-number,
.step-item.completed .step-number {
  background-color: rgba(255, 255, 255, 0.2);
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 600;
  font-size: var(--text-sm);
}

.step-description {
  font-size: var(--text-xs);
  opacity: 0.8;
  margin-top: var(--spacing-1);
}

.step-content {
  margin-bottom: var(--spacing-6);
}

.step-subtitle {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-6);
}

.regions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-4);
}

.region-card {
  padding: var(--spacing-4);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.region-card:hover {
  border-color: var(--color-primary);
}

.region-card.selected {
  border-color: var(--color-primary);
  background-color: rgba(59, 130, 246, 0.05);
}

.region-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-2);
}

.region-header h4 {
  margin: 0;
}

.region-checkbox {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.region-checkbox.checked {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.region-description {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-1);
}

.region-bbox {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.thresholds-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.threshold-item {
  padding: var(--spacing-4);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
}

.threshold-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.threshold-value {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-primary);
}

.threshold-slider {
  width: 100%;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-border);
  border-radius: var(--radius-full);
  outline: none;
}

.threshold-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  cursor: pointer;
}

.threshold-labels {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-top: var(--spacing-2);
}

.threshold-preview {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-top: var(--spacing-2);
  font-style: italic;
}

.shipments-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.shipment-item {
  padding: var(--spacing-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.shipment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
}

.review-section {
  margin-bottom: var(--spacing-6);
}

.review-section h3 {
  margin-bottom: var(--spacing-2);
  font-size: var(--text-base);
}

.review-value {
  font-size: var(--text-lg);
  font-weight: 500;
}

.review-regions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.review-thresholds {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.threshold-summary {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-2) var(--spacing-3);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.review-shipments {
  list-style: none;
  padding: 0;
}

.review-shipments li {
  padding: var(--spacing-2);
  border-bottom: 1px solid var(--color-border);
}

.step-actions {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-3);
}

.mt-6 {
  margin-top: var(--spacing-6);
}

.mb-4 {
  margin-bottom: var(--spacing-4);
}

.text-secondary {
  color: var(--color-text-secondary);
}
</style>