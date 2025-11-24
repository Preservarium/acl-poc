#!/bin/bash

set -e

BASE_URL="http://localhost:8000/api"

echo "============================================"
echo "ACL POC - Phase 2 API Testing"
echo "============================================"
echo ""

# Test 1: Login as admin
echo "[1] Login as admin..."
TOKEN=$(curl -s -X POST $BASE_URL/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token obtained: ${TOKEN:0:50}..."
echo ""

# Test 2: Get current user
echo "[2] Get current user..."
curl -s -X GET $BASE_URL/auth/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Test 3: Create a site
echo "[3] Create site..."
SITE_RESPONSE=$(curl -s -X POST $BASE_URL/sites \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name": "Factory 1"}')
echo "$SITE_RESPONSE" | python3 -m json.tool
SITE_ID=$(echo "$SITE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Site ID: $SITE_ID"
echo ""

# Test 4: List sites
echo "[4] List sites..."
curl -s -X GET $BASE_URL/sites \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Test 5: Create a plan
echo "[5] Create plan..."
PLAN_RESPONSE=$(curl -s -X POST $BASE_URL/plans \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\": \"Floor 1\", \"site_id\": \"$SITE_ID\"}")
echo "$PLAN_RESPONSE" | python3 -m json.tool
PLAN_ID=$(echo "$PLAN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Plan ID: $PLAN_ID"
echo ""

# Test 6: Create a sensor
echo "[6] Create sensor..."
SENSOR_RESPONSE=$(curl -s -X POST $BASE_URL/sensors \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\": \"Sensor 001\", \"plan_id\": \"$PLAN_ID\"}")
echo "$SENSOR_RESPONSE" | python3 -m json.tool
SENSOR_ID=$(echo "$SENSOR_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Sensor ID: $SENSOR_ID"
echo ""

# Test 7: List my permissions (first 2)
echo "[7] List my permissions..."
curl -s -X GET $BASE_URL/permissions \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; perms = json.load(sys.stdin); print(json.dumps(perms[:2], indent=2))"
echo ""

# Test 8: Bulk permission check
echo "[8] Bulk permission check..."
curl -s -X POST $BASE_URL/permissions/check \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"checks\": [{\"resource_type\": \"site\", \"resource_id\": \"$SITE_ID\", \"permission\": \"read\"}, {\"resource_type\": \"plan\", \"resource_id\": \"$PLAN_ID\", \"permission\": \"write\"}, {\"resource_type\": \"sensor\", \"resource_id\": \"$SENSOR_ID\", \"permission\": \"delete\"}]}" | python3 -m json.tool
echo ""

# Test 9: Login as alice
echo "[9] Login as alice..."
ALICE_TOKEN=$(curl -s -X POST $BASE_URL/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "alice123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Alice token obtained"
echo ""

# Test 10: Alice tries to list sites (should be empty)
echo "[10] Alice lists sites (should be empty - no permissions)..."
curl -s -X GET $BASE_URL/sites \
  -H "Authorization: Bearer $ALICE_TOKEN" | python3 -m json.tool
echo ""

echo "============================================"
echo "Testing Complete!"
echo "============================================"
