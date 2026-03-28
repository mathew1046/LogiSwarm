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
import { ref, computed, onMounted } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'

const analyticsStore = useAnalyticsStore()

const timeRange = ref('30d')
const timeRangeOptions = [
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: '90d', label: 'Last 90 Days' },
]

const loading = computed(() => analyticsStore.loading)
const summary = computed(() => analyticsStore.summary)
const timeline = computed(() => analyticsStore.timeline)
const severityDistribution = computed(() => analyticsStore.severityDistribution)
const regionMetrics = computed(() => analyticsStore.regionMetrics)
const accuracyTimeline = computed(() => analyticsStore.accuracyTimeline)

const severityColors = {
  LOW: '#22c55e',
  MEDIUM: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444'
}

const decisionColors = {
  auto_act: '#22c55e',
  recommend: '#f59e0b',
  monitor: '#3b82f6'
}

function formatNumber(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
  return num.toString()
}

function formatPercent(num) {
  return (num * 100).toFixed(1) + '%'
}

async function refreshData() {
  await analyticsStore.fetchAll(timeRange.value)
}

function changeTimeRange(range) {
  timeRange.value = range
  refreshData()
}

onMounted(() => {
  refreshData()
})
</script>

<template>
  <div class="analytics-dashboard">
    <div class="dashboard-header">
      <h1>Analytics Dashboard</h1>
      <div class="time-range-picker">
        <button
          v-for="option in timeRangeOptions"
          :key="option.value"
          :class="['time-btn', { 'time-btn--active': timeRange === option.value }]"
          @click="changeTimeRange(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="loading__spinner"></div>
    </div>

    <div v-else class="dashboard-content">
      <div class="summary-cards">
        <div class="summary-card">
          <div class="summary-card__icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <div class="summary-card__content">
            <span class="summary-card__label">Total Disruptions</span>
            <span class="summary-card__value">{{ formatNumber(summary?.total_disruptions || 0) }}</span>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-card__icon summary-card__icon--success">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div class="summary-card__content">
            <span class="summary-card__label">Overall Accuracy</span>
            <span class="summary-card__value">{{ formatPercent(summary?.overall_accuracy || 0) }}</span>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-card__icon summary-card__icon--warning">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div class="summary-card__content">
            <span class="summary-card__label">Avg Detection Time</span>
            <span class="summary-card__value">{{ summary?.avg_time_to_detection_hours || 0 }}h</span>
          </div>
        </div>

        <div class="summary-card">
          <div class="summary-card__icon summary-card__icon--info">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
          </div>
          <div class="summary-card__content">
            <span class="summary-card__label">Regions Monitored</span>
            <span class="summary-card__value">{{ summary?.total_regions || 0 }}</span>
          </div>
        </div>
      </div>

      <div class="charts-row">
        <div class="chart-card">
          <h3>Severity Distribution</h3>
          <div class="donut-chart">
            <svg viewBox="0 0 200 200" class="donut-svg">
              <circle
                v-for="(segment, index) in severityDistribution"
                :key="segment.severity"
                cx="100"
                cy="100"
                r="70"
                fill="transparent"
                :stroke="severityColors[segment.severity]"
                stroke-width="30"
                :stroke-dasharray="`${segment.percentage * 4.4} ${440 - segment.percentage * 4.4}`"
                :stroke-dashoffset="-getOffset(index)"
              />
            </svg>
            <div class="donut-center">
              <span class="donut-total">{{ formatNumber(summary?.decision_breakdown?.total || 0) }}</span>
              <span class="donut-label">Total</span>
            </div>
          </div>
          <div class="severity-legend">
            <div v-for="segment in severityDistribution" :key="segment.severity" class="legend-item">
              <span class="legend-color" :style="{ backgroundColor: severityColors[segment.severity] }"></span>
              <span class="legend-label">{{ segment.severity }}</span>
              <span class="legend-value">{{ segment.count }}</span>
            </div>
          </div>
        </div>

        <div class="chart-card">
          <h3>Decision Breakdown</h3>
          <div class="bar-chart">
            <div class="bar-container">
              <div class="decision-bar">
                <div
                  class="bar-segment bar-segment--auto"
                  :style="{ width: getDecisionPercent('auto_act') + '%' }"
                  :title="`Auto-Act: ${summary?.decision_breakdown?.auto_act || 0}`"
                ></div>
                <div
                  class="bar-segment bar-segment--recommend"
                  :style="{ width: getDecisionPercent('recommend') + '%' }"
                  :title="`Recommend: ${summary?.decision_breakdown?.recommend || 0}`"
                ></div>
                <div
                  class="bar-segment bar-segment--monitor"
                  :style="{ width: getDecisionPercent('monitor') + '%' }"
                  :title="`Monitor: ${summary?.decision_breakdown?.monitor || 0}`"
                ></div>
              </div>
            </div>
          </div>
          <div class="decision-legend">
            <div class="legend-item">
              <span class="legend-color" style="background-color: #22c55e"></span>
              <span class="legend-label">Auto-Act</span>
              <span class="legend-value">{{ summary?.decision_breakdown?.auto_act || 0 }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-color" style="background-color: #f59e0b"></span>
              <span class="legend-label">Recommend</span>
              <span class="legend-value">{{ summary?.decision_breakdown?.recommend || 0 }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-color" style="background-color: #3b82f6"></span>
              <span class="legend-label">Monitor</span>
              <span class="legend-value">{{ summary?.decision_breakdown?.monitor || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="region-metrics">
        <h3>Region Performance</h3>
        <div class="metrics-table">
          <div class="metrics-table__header">
            <div class="metrics-table__cell">Region</div>
            <div class="metrics-table__cell">Disruptions</div>
            <div class="metrics-table__cell">MTTD (h)</div>
            <div class="metrics-table__cell">Accuracy</div>
          </div>
          <div
            v-for="metric in regionMetrics"
            :key="metric.region_id"
            class="metrics-table__row"
          >
            <div class="metrics-table__cell">{{ metric.region_name }}</div>
            <div class="metrics-table__cell">{{ metric.disruption_count }}</div>
            <div class="metrics-table__cell">{{ metric.mean_time_to_detection_hours.toFixed(1) }}</div>
            <div class="metrics-table__cell">
              <div class="accuracy-bar">
                <div class="accuracy-bar__fill" :style="{ width: metric.accuracy_score * 100 + '%' }"></div>
              </div>
              <span class="accuracy-value">{{ formatPercent(metric.accuracy_score) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics-dashboard {
  padding: var(--spacing-6);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
}

.dashboard-header h1 {
  margin: 0;
}

.time-range-picker {
  display: flex;
  gap: var(--spacing-2);
}

.time-btn {
  padding: var(--spacing-2) var(--spacing-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background-color: var(--color-bg);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.time-btn:hover {
  border-color: var(--color-primary);
}

.time-btn--active {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-12);
}

.loading__spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.summary-card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.summary-card__icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background-color: var(--color-bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
}

.summary-card__icon--success { color: var(--color-success); }
.summary-card__icon--warning { color: var(--color-warning); }
.summary-card__icon--info { color: var(--color-primary); }

.summary-card__content {
  display: flex;
  flex-direction: column;
}

.summary-card__label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.summary-card__value {
  font-size: var(--text-xl);
  font-weight: 700;
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.chart-card {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
}

.chart-card h3 {
  margin: 0 0 var(--spacing-4);
  font-size: var(--text-lg);
}

.donut-chart {
  position: relative;
  width: 200px;
  height: 200px;
  margin: 0 auto;
}

.donut-svg {
  transform: rotate(-90deg);
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.donut-total {
  display: block;
  font-size: var(--text-2xl);
  font-weight: 700;
}

.donut-label {
  display: block;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.severity-legend,
.decision-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-top: var(--spacing-4);
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.legend-value {
  font-size: var(--text-xs);
  font-weight: 600;
}

.bar-chart {
  padding: var(--spacing-4);
}

.bar-container {
  height: 32px;
}

.decision-bar {
  height: 100%;
  display: flex;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.bar-segment {
  height: 100%;
  transition: width var(--transition-normal);
}

.bar-segment--auto { background-color: #22c55e; }
.bar-segment--recommend { background-color: #f59e0b; }
.bar-segment--monitor { background-color: #3b82f6; }

.region-metrics {
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
}

.region-metrics h3 {
  margin: 0 0 var(--spacing-4);
}

.metrics-table {
  width: 100%;
}

.metrics-table__header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 2fr;
  gap: var(--spacing-2);
  padding: var(--spacing-2);
  background-color: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: var(--text-sm);
}

.metrics-table__row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 2fr;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-2);
  border-bottom: 1px solid var(--color-border);
  align-items: center;
}

.metrics-table__row:last-child {
  border-bottom: none;
}

.accuracy-bar {
  height: 8px;
  background-color: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  display: inline-block;
  width: 100px;
  margin-right: var(--spacing-2);
}

.accuracy-bar__fill {
  height: 100%;
  background-color: var(--color-success);
  border-radius: var(--radius-full);
}

.accuracy-value {
  font-size: var(--text-sm);
  font-weight: 600;
}
</style>