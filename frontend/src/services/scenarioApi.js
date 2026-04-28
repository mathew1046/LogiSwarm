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

const BASE_URL = '/api/scenarios'

/**
 * List all historical scenarios with optional category filtering
 * @param {string|null} category - Optional category filter
 * @returns {Promise<Array>} List of scenarios
 */
export async function listScenarios(category = null) {
  const url = category ? `${BASE_URL}?category=${encodeURIComponent(category)}` : BASE_URL
  const response = await fetch(url)
  const data = await response.json()
  if (data.error) {
    throw new Error(data.error)
  }
  return data.data || []
}

/**
 * Get a specific scenario by ID
 * @param {string} id - Scenario ID
 * @returns {Promise<Object>} Scenario data
 */
export async function getScenario(id) {
  const response = await fetch(`${BASE_URL}/${encodeURIComponent(id)}`)
  const data = await response.json()
  if (data.error) {
    throw new Error(data.error)
  }
  return data.data
}

/**
 * Run a simulation using a historical scenario
 * @param {string} id - Scenario ID
 * @returns {Promise<Object>} Simulation report
 */
export async function runScenario(id) {
  const response = await fetch(`${BASE_URL}/${encodeURIComponent(id)}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  const data = await response.json()
  if (data.error) {
    throw new Error(data.error)
  }
  return data.data
}

/**
 * List all scenario categories with counts
 * @returns {Promise<Array>} List of categories with counts
 */
export async function listCategories() {
  const response = await fetch(`${BASE_URL}/categories`)
  const data = await response.json()
  if (data.error) {
    throw new Error(data.error)
  }
  return data.data || []
}