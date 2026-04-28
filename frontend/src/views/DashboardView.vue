<script setup>
import { computed, onMounted, ref } from 'vue'
import ProjectLayout from '@/components/layout/ProjectLayout.vue'
import { useSimpleAppStore } from '@/stores/simpleApp'

const simpleAppStore = useSimpleAppStore()
const origin = ref('')
const destination = ref('')

const canSave = computed(() => origin.value && destination.value && origin.value !== destination.value)

async function saveShipment() {
  if (!canSave.value) return
  await simpleAppStore.saveShipment(origin.value, destination.value)
}

onMounted(async () => {
  await simpleAppStore.bootstrap()
  if (simpleAppStore.shipment) {
    origin.value = simpleAppStore.shipment.origin
    destination.value = simpleAppStore.shipment.destination
  }
})
</script>

<template>
  <ProjectLayout>
    <div class="page-stack">
      <div class="page-header">
        <h1>Dashboard</h1>
        <p class="muted">Choose a shipment origin and destination from the 10 supported places.</p>
      </div>

      <div class="card form-card">
        <div class="form-grid">
          <div class="form-group">
            <label class="label">Origin</label>
            <select v-model="origin" class="input">
              <option value="">Select origin</option>
              <option v-for="place in simpleAppStore.places" :key="place.id" :value="place.id">{{ place.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="label">Destination</label>
            <select v-model="destination" class="input">
              <option value="">Select destination</option>
              <option v-for="place in simpleAppStore.places" :key="place.id" :value="place.id">{{ place.name }}</option>
            </select>
          </div>
        </div>
        <div class="action-row">
          <button class="btn btn--primary" :disabled="!canSave || simpleAppStore.loading" @click="saveShipment">
            {{ simpleAppStore.loading ? 'Saving...' : 'Save Shipment' }}
          </button>
        </div>
      </div>

      <div v-if="simpleAppStore.shipment" class="card">
        <div class="card-label">Saved Shipment</div>
        <h2>{{ simpleAppStore.shipment.origin_name }} → {{ simpleAppStore.shipment.destination_name }}</h2>
        <p class="muted">Updated {{ new Date(simpleAppStore.shipment.updated_at).toLocaleString() }}</p>
      </div>

      <div v-if="simpleAppStore.error" class="card error-card">
        {{ simpleAppStore.error }}
      </div>
    </div>
  </ProjectLayout>
</template>

<style scoped>
.page-stack { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { display: flex; flex-direction: column; gap: 0.35rem; }
.muted { color: var(--color-text-secondary); }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.action-row { margin-top: 1rem; display: flex; justify-content: flex-end; }
.error-card { color: var(--color-error); }
@media (max-width: 700px) { .form-grid { grid-template-columns: 1fr; } }
</style>
