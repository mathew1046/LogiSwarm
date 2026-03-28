#!/bin/bash

# Comprehensive API Test for LogiSwarm

echo "=== LogiSwarm API Comprehensive Test ==="
echo ""

BASE_URL="http://localhost:5001"

# Test 1: Health check
echo "✓ Test 1: Health Check"
HEALTH=$(curl -s "$BASE_URL/health")
echo "$HEALTH" | jq -e '.status == "ok"' > /dev/null && echo "  PASS" || echo "  FAIL: $HEALTH"
echo ""

# Test 2: Create a project
echo "✓ Test 2: Create Project"
PROJECT_RESPONSE=$(curl -s -X POST "$BASE_URL/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Test Project",
    "description": "Testing all API endpoints",
    "region_ids": ["gulf_suez", "se_asia", "europe"]
  }')
PROJECT_ID=$(echo "$PROJECT_RESPONSE" | jq -r '.data.id // empty')
if [ -n "$PROJECT_ID" ]; then
    echo "  PASS - Created project ID: $PROJECT_ID"
else
    echo "  FAIL: $PROJECT_RESPONSE"
fi
echo ""

if [ -n "$PROJECT_ID" ]; then
    # Test 3: Get project
    echo "✓ Test 3: Get Project"
    curl -s "$BASE_URL/projects/$PROJECT_ID" | jq -e '.data.id' > /dev/null && echo "  PASS" || echo "  FAIL"
    echo ""
    
    # Test 4: List all projects
    echo "✓ Test 4: List All Projects"
    curl -s "$BASE_URL/projects" | jq -e '.data | length >= 1' > /dev/null && echo "  PASS" || echo "  FAIL"
    echo ""
    
    # Test 5: Get agents for project
    echo "✓ Test 5: Get Project Agents"
    curl -s "$BASE_URL/projects/$PROJECT_ID/agents" | jq -e '.data' > /dev/null && echo "  PASS" || echo "  FAIL"
    echo ""
fi

# Test 6: Get agent status (gulf_suez)
echo "✓ Test 6: Get Agent Status (gulf_suez)"
curl -s "$BASE_URL/agents/gulf_suez" | jq -e '.data.region_id' > /dev/null && echo "  PASS" || echo "  FAIL"
echo ""

# Test 7: Get all agents
echo "✓ Test 7: List All Agents"
curl -s "$BASE_URL/agents" | jq -e '.data | length >= 1' > /dev/null && echo "  PASS" || echo "  FAIL"
echo ""

# Test 8: Get disruptions
echo "✓ Test 8: Get Disruptions"
curl -s "$BASE_URL/disruptions" | jq -e '.data' > /dev/null && echo "  PASS" || echo "  FAIL"
echo ""

# Test 9: Create a disruption
echo "✓ Test 9: Create Disruption"
DISRUPTION=$(curl -s -X POST "$BASE_URL/disruptions" \
  -H "Content-Type: application/json" \
  -d '{
    "region_id": "gulf_suez",
    "severity": "high",
    "signal_type": "weather_alert",
    "description": "Test weather disruption"
  }')
echo "$DISRUPTION" | jq -e '.data.id // .id' > /dev/null && echo "  PASS" || echo "  FAIL: $DISRUPTION"
echo ""

# Test 10: Get analytics summary
echo "✓ Test 10: Get Analytics Summary"
curl -s "$BASE_URL/analytics/summary" | jq -e '.data' > /dev/null && echo "  PASS" || echo "  FAIL"
echo ""

# Test 11: Get recommendations
echo "✓ Test 11: Get Recommendations"
if [ -n "$PROJECT_ID" ]; then
    curl -s "$BASE_URL/projects/$PROJECT_ID/recommendations" | jq -e '.data' > /dev/null && echo "  PASS" || echo "  FAIL"
else
    echo "  SKIP - No project ID"
fi
echo ""

# Test 12: Get routes
echo "✓ Test 12: Get Routes"
if [ -n "$PROJECT_ID" ]; then
    curl -s "$BASE_URL/projects/$PROJECT_ID/routes" | jq -e '.data' > /dev/null && echo "  PASS" || echo "  FAIL"
else
    echo "  SKIP - No project ID"
fi
echo ""

# Test 13: Get feed events
echo "✓ Test 13: Get Feed Events"
if [ -n "$PROJECT_ID" ]; then
    curl -s "$BASE_URL/projects/$PROJECT_ID/feeds/events" | jq -e '.data' > /dev/null && echo "  PASS" || echo "  FAIL"
else
    echo "  SKIP - No project ID"
fi
echo ""

# Test 14: Interview agent
echo "✓ Test 14: Interview Agent (gulf_suez)"
INTERVIEW=$(curl -s -X POST "$BASE_URL/agents/gulf_suez/interview" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your current status?"
  }')
echo "$INTERVIEW" | jq -e '.region_id // .data.region_id' > /dev/null && echo "  PASS" || echo "  FAIL: $INTERVIEW"
echo ""

# Test 15: Get metrics
echo "✓ Test 15: Get Prometheus Metrics"
curl -s "$BASE_URL/metrics" | grep -q "logiswarm" && echo "  PASS" || echo "  FAIL"
echo ""

# Test 16: Get API docs
echo "✓ Test 16: API Documentation"
curl -s "$BASE_URL/docs" | grep -q "swagger" && echo "  PASS" || echo "  FAIL"
echo ""

echo "=== API Testing Complete ==="
echo ""
echo "Summary:"
echo "- Backend Version: $(curl -s $BASE_URL/health | jq -r '.version')"
echo "- Project Created: ${PROJECT_ID:-None}"
echo ""
echo "Services:"
echo "- Backend: http://localhost:5001"
echo "- API Docs: http://localhost:5001/docs"
echo "- Metrics: http://localhost:5001/metrics"
echo ""
echo "Note: Some endpoints may return empty data if agents are still initializing."