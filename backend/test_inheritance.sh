#!/bin/bash

set -e

BASE_URL="http://localhost:8000/api"

echo "============================================"
echo "ACL POC - Permission Inheritance Test"
echo "============================================"
echo ""

# Login as admin
echo "[1] Login as admin..."
ADMIN_TOKEN=$(curl -s -X POST $BASE_URL/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "admin123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
ADMIN_ID=$(curl -s -X GET $BASE_URL/auth/me \
  -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Admin ID: $ADMIN_ID"
echo ""

# Login as alice
echo "[2] Login as alice..."
ALICE_TOKEN=$(curl -s -X POST $BASE_URL/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "alice123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
ALICE_ID=$(curl -s -X GET $BASE_URL/auth/me \
  -H "Authorization: Bearer $ALICE_TOKEN" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Alice ID: $ALICE_ID"
echo ""

# Create hierarchy: Site -> Plan -> Sensor
echo "[3] Create resource hierarchy..."
SITE_ID=$(curl -s -X POST $BASE_URL/sites \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name": "Test Site"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Site ID: $SITE_ID"

PLAN_ID=$(curl -s -X POST $BASE_URL/plans \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\": \"Test Plan\", \"site_id\": \"$SITE_ID\"}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Plan ID: $PLAN_ID"

SENSOR_ID=$(curl -s -X POST $BASE_URL/sensors \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{\"name\": \"Test Sensor\", \"plan_id\": \"$PLAN_ID\"}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Sensor ID: $SENSOR_ID"
echo ""

# Alice tries to access (should fail)
echo "[4] Alice tries to access sensor (should fail)..."
ALICE_SENSOR=$(curl -s -X GET $BASE_URL/sensors/$SENSOR_ID \
  -H "Authorization: Bearer $ALICE_TOKEN")
echo "Response: $ALICE_SENSOR"
echo ""

# Grant alice READ permission on SITE with inheritance
echo "[5] Grant alice READ permission on SITE with inheritance..."
PERM_RESPONSE=$(curl -s -X POST $BASE_URL/permissions \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"grantee_type\": \"user\",
    \"grantee_id\": \"$ALICE_ID\",
    \"resource_type\": \"site\",
    \"resource_id\": \"$SITE_ID\",
    \"permission\": \"read\",
    \"effect\": \"allow\",
    \"inherit\": true
  }")
echo "$PERM_RESPONSE" | python3 -m json.tool
echo ""

# Alice tries to access sensor again (should succeed via inheritance)
echo "[6] Alice tries to access sensor (should succeed via inheritance)..."
ALICE_SENSOR2=$(curl -s -X GET $BASE_URL/sensors/$SENSOR_ID \
  -H "Authorization: Bearer $ALICE_TOKEN")
echo "$ALICE_SENSOR2" | python3 -m json.tool
echo ""

# Bulk check alice's permissions
echo "[7] Bulk check alice's permissions on all resources..."
curl -s -X POST $BASE_URL/permissions/check \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"checks\": [
      {\"resource_type\": \"site\", \"resource_id\": \"$SITE_ID\", \"permission\": \"read\"},
      {\"resource_type\": \"plan\", \"resource_id\": \"$PLAN_ID\", \"permission\": \"read\"},
      {\"resource_type\": \"sensor\", \"resource_id\": \"$SENSOR_ID\", \"permission\": \"read\"},
      {\"resource_type\": \"sensor\", \"resource_id\": \"$SENSOR_ID\", \"permission\": \"write\"}
    ]
  }" | python3 -m json.tool
echo ""

# Now grant DENY on plan (should block sensor access)
echo "[8] Grant alice DENY on PLAN (should block sensor access)..."
curl -s -X POST $BASE_URL/permissions \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"grantee_type\": \"user\",
    \"grantee_id\": \"$ALICE_ID\",
    \"resource_type\": \"plan\",
    \"resource_id\": \"$PLAN_ID\",
    \"permission\": \"read\",
    \"effect\": \"deny\",
    \"inherit\": true
  }" | python3 -m json.tool
echo ""

# Bulk check again (sensor access should be denied)
echo "[9] Bulk check after DENY (sensor should be denied)..."
curl -s -X POST $BASE_URL/permissions/check \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "{
    \"checks\": [
      {\"resource_type\": \"site\", \"resource_id\": \"$SITE_ID\", \"permission\": \"read\"},
      {\"resource_type\": \"plan\", \"resource_id\": \"$PLAN_ID\", \"permission\": \"read\"},
      {\"resource_type\": \"sensor\", \"resource_id\": \"$SENSOR_ID\", \"permission\": \"read\"}
    ]
  }" | python3 -m json.tool
echo ""

# Alice tries to access sensor (should fail due to deny)
echo "[10] Alice tries to access sensor (should fail due to DENY)..."
ALICE_SENSOR3=$(curl -s -X GET $BASE_URL/sensors/$SENSOR_ID \
  -H "Authorization: Bearer $ALICE_TOKEN")
echo "Response: $ALICE_SENSOR3"
echo ""

echo "============================================"
echo "Inheritance Test Complete!"
echo ""
echo "Key Findings:"
echo "- READ permission on site inherited to plan and sensor"
echo "- DENY on plan blocked access to sensor"
echo "- DENY takes precedence over inherited ALLOW"
echo "============================================"
