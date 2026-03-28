#!/bin/bash

# Test LogiSwarm API endpoints

echo "=== Testing LogiSwarm API ==="
echo ""

BASE_URL="http://localhost:5001"

# Test 1: Health check
echo "Test 1: Health Check"
curl -s "$BASE_URL/health" | jq . || echo "Failed"
echo ""

# Test 2: API Documentation
echo "Test 2: API Docs"
curl -s "$BASE_URL/docs" > /dev/null && echo "Docs available" || echo "Failed"
echo ""

# Test 3: Create a project
echo "Test 3: Create Project"
PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "Testing API endpoints",
    "region_ids": ["gulf_suez", "se_asia"]
  }')
echo "$PROJECT_RESPONSE" | jq . || echo "Failed"
echo ""

# Extract project ID
PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.data.id // .id // empty')
if [ -n "$PROJECT_ID" ]; then
    echo "Created project ID: $PROJECT_ID"
    
    # Test 4: Get project
    echo "Test 4: Get Project"
    curl -s "$BASE_URL/api/projects/$PROJECT_ID" | jq . || echo "Failed"
    echo ""
    
    # Test 5: List agents for project
    echo "Test 5: List Agents"
    curl -s "$BASE_URL/api/projects/$PROJECT_ID/agents" | jq . || echo "Failed"
    echo ""
    
    # Test 6: Get agent status
    echo "Test 6: Get Agent Status (gulf_suez)"
    curl -s "$BASE_URL/api/agents/gulf_suez" | jq . || echo "Failed"
    echo ""
    
    # Test 7: Get feed events
    echo "Test 7: Get Feed Events"
    curl -s "$BASE_URL/api/projects/$PROJECT_ID/feeds/events" | jq . || echo "Failed"
    echo ""
    
    # Test 8: Get disruptions
    echo "Test 8: Get Disruptions"
    curl -s "$BASE_URL/api/projects/$PROJECT_ID/disruptions" | jq . || echo "Failed"
    echo ""
    
    # Test 9: Create a disruption (simulated)
    echo "Test 9: Create Disruption"
    curl -s -X POST "$BASE_URL/api/disruptions" \
      -H "Content-Type: application/json" \
      -d '{
        "region_id": "gulf_suez",
        "severity": "high",
        "signal_type": "weather_alert",
        "description": "Test disruption"
      }' | jq . || echo "Failed"
    echo ""
    
    # Test 10: Get analytics
    echo "Test 10: Get Analytics Summary"
    curl -s "$BASE_URL/api/analytics/summary" | jq . || echo "Failed"
    echo ""
    
    # Test 11: Get recommendations
    echo "Test 11: Get Recommendations"
    curl -s "$BASE_URL/api/projects/$PROJECT_ID/recommendations" | jq . || echo "Failed"
    echo ""
    
    # Test 12: Get metrics
    echo "Test 12: Get Prometheus Metrics"
    curl -s "$BASE_URL/metrics" | head -20 || echo "Failed"
    echo ""
    
    # Test 13: Interview agent
    echo "Test 13: Interview Agent"
    curl -s -X POST "$BASE_URL/api/agents/gulf_suez/interview" \
      -H "Content-Type: application/json" \
      -d '{
        "question": "What is the current status of the Suez Canal?"
      }' | jq . || echo "Failed"
    echo ""
fi

echo "=== API Testing Complete ==="