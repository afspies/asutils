#!/bin/bash
# Quick test script to verify Conductor configuration
# Run this to test if your Portkey API key and gateway are working

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Testing Conductor Configuration"
echo "================================"
echo ""

# Check for API key argument
if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <PORTKEY_API_KEY>${NC}"
    echo "Example: $0 xjlCml66ahXsY/fbg9Al7G6gnrcR"
    exit 1
fi

API_KEY="$1"
GATEWAY_URL="https://live.ai.epicgames.com"

echo "Testing configuration:"
echo "  Gateway: $GATEWAY_URL"
echo "  API Key: ${API_KEY:0:10}..."
echo ""

# Test 1: Basic connectivity
echo -e "${YELLOW}[1/3]${NC} Testing gateway connectivity..."
if curl -s -I --max-time 5 "$GATEWAY_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Gateway is reachable"
else
    echo -e "${RED}✗${NC} Cannot reach gateway"
    exit 1
fi

# Test 2: API key validation (with correct headers)
echo -e "${YELLOW}[2/3]${NC} Testing API key without x-portkey-config..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --max-time 10 \
    -X POST "$GATEWAY_URL/v1/messages" \
    -H "Content-Type: application/json" \
    -H "x-portkey-api-key: $API_KEY" \
    -H "x-portkey-debug: true" \
    -H "x-vertex-ai-llm-request-type: shared" \
    -H "anthropic-version: 2023-06-01" \
    -d '{"model":"claude-sonnet-4","max_tokens":5,"messages":[{"role":"user","content":"Hi"}]}' \
    2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓${NC} API key validated successfully"
    echo "  Response: $(echo "$BODY" | jq -r '.content[0].text' 2>/dev/null || echo "$BODY")"
else
    echo -e "${RED}✗${NC} API key validation failed (HTTP $HTTP_CODE)"
    echo "  Response: $BODY"
    exit 1
fi

# Test 3: Verify x-portkey-config causes error
echo -e "${YELLOW}[3/3]${NC} Verifying x-portkey-config is NOT needed..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --max-time 10 \
    -X POST "$GATEWAY_URL/v1/messages" \
    -H "Content-Type: application/json" \
    -H "x-portkey-config: pc-claude-60f174" \
    -H "x-portkey-api-key: $API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -d '{"model":"claude-sonnet-4","max_tokens":5,"messages":[{"role":"user","content":"Hi"}]}' \
    2>/dev/null)

HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

if [ "$HTTP_CODE" = "400" ] && echo "$BODY" | grep -q "Cannot override"; then
    echo -e "${GREEN}✓${NC} Confirmed: x-portkey-config should NOT be used"
    echo "  (Your API key has a default config)"
else
    echo -e "${YELLOW}⚠${NC} Unexpected: x-portkey-config didn't fail as expected"
    echo "  This may work for your key, but generally should be omitted"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Configuration Verified! ✓${NC}"
echo -e "${GREEN}════════════════════════════════════════════════${NC}"
echo ""
echo "Use this configuration in Conductor Settings → Env:"
echo ""
echo "ANTHROPIC_BASE_URL=$GATEWAY_URL"
echo "ANTHROPIC_AUTH_TOKEN=test"
echo "ANTHROPIC_CUSTOM_HEADERS=x-portkey-api-key: $API_KEY"
echo "x-portkey-debug: true"
echo "x-vertex-ai-llm-request-type: shared"
echo ""
echo -e "${YELLOW}Important: Do NOT include x-portkey-config header${NC}"
