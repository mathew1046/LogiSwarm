<script setup>
import { ref } from 'vue'
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
  { id: 'se_asia', name: 'SE Asia', description: 'Malacca Strait, Singapore hub' },
  { id: 'europe', name: 'Europe', description: 'Rotterdam-Hamburg-Antwerp corridor' },
  { id: 'gulf_suez', name: 'Gulf/Suez', description: 'Suez Canal, Persian Gulf' },
  { id: 'north_america', name: 'North America', description: 'US West Coast, Panama' },
  { id: 'china_ea', name: 'China/East Asia', description: 'Shanghai-Ningbo-Busan cluster' }
]

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

async function submitProject() {
  loading.value = true
  try {
    const project = await projectStore.createProject({
      name: projectName.value,
      config: {
        regions: selectedRegions.value,
        thresholds: thresholds.value
      }
    })
    if (project) {
      router.push(`/projects/${project.id}`)
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <ProjectLayout>
    <div>
      <h1>Create Project</h1>
      
      <div class="step-indicator">
        <div v-for="s in 4" :key="s" :class="['step', { active: step === s, completed: step > s }]">
          {{ s }}
        </div>
      </div>
      
      <div v-if="step === 1" class="card">
        <h2>Step 1: Project Name</h2>
        <div class="form-group">
          <label class="label">Project Name</label>
          <input v-model="projectName" type="text" class="input" placeholder="Enter project name" />
        </div>
        <button class="btn btn--primary" @click="step = 2" :disabled="!projectName">Next</button>
      </div>
      
      <div v-else-if="step === 2" class="card">
        <h2>Step 2: Select Regions</h2>
        <div class="grid grid--2">
          <div 
            v-for="region in regions" 
            :key="region.id" 
            :class="['card', { selected: selectedRegions.includes(region.id) }]"
            @click="toggleRegion(region.id)"
          >
            <h3>{{ region.name }}</h3>
            <p>{{ region.description }}</p>
          </div>
        </div>
        <div class="actions">
          <button class="btn btn--secondary" @click="step = 1">Back</button>
          <button class="btn btn--primary" @click="step = 3" :disabled="selectedRegions.length === 0">Next</button>
        </div>
      </div>
      
      <div v-else-if="step === 3" class="card">
        <h2>Step 3: Configure Thresholds</h2>
        <div v-for="regionId in selectedRegions" :key="regionId" class="form-group">
          <label class="label">{{ regions.find(r => r.id === regionId)?.name }} Threshold</label>
          <input 
            v-model.number="thresholds[regionId]" 
            type="range" 
            min="0.5" 
            max="0.95" 
            step="0.05" 
            class="input"
          />
          <span>{{ (thresholds[regionId] || 0.75).toFixed(2) }}</span>
        </div>
        <div class="actions">
          <button class="btn btn--secondary" @click="step = 2">Back</button>
          <button class="btn btn--primary" @click="step = 4">Next</button>
        </div>
      </div>
      
      <div v-else-if="step === 4" class="card">
        <h2>Step 4: Review</h2>
        <p><strong>Name:</strong> {{ projectName }}</p>
        <p><strong>Regions:</strong> {{ selectedRegions.map(id => regions.find(r => r.id === id)?.name).join(', ') }}</p>
        <div class="actions">
          <button class="btn btn--secondary" @click="step = 3">Back</button>
          <button class="btn btn--primary" @click="submitProject" :disabled="loading">
            {{ loading ? 'Creating...' : 'Create Project' }}
          </button>
        </div>
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.step-indicator {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-6);
}

.step {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background-color: var(--color-bg-tertiary);
  color: var(--color-text-secondary);
}

.step.active {
  background-color: var(--color-primary);
  color: var(--color-text-inverse);
}

.step.completed {
  background-color: var(--color-success);
  color: var(--color-text-inverse);
}

.card.selected {
  border-color: var(--color-primary);
  background-color: rgba(59, 130, 246, 0.05);
}

.actions {
  display: flex;
  gap: var(--spacing-3);
  margin-top: var(--spacing-4);
}
</style>