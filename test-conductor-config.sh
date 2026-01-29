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

# Test 2: API key validation and config check
echo -e "${YELLOW}[2/3]${NC} Testing API key and checking config..."
RESPONSE=$(curl -s --max-time 10 \
    -X POST "$GATEWAY_URL/v1/messages" \
    -H "Content-Type: application/json" \
    -H "x-portkey-api-key: $API_KEY" \
    -H "x-portkey-debug: true" \
    -H "x-vertex-ai-llm-request-type: shared" \
    -H "anthropic-version: 2023-06-01" \
    -d '{"model":"claude-opus-4","max_tokens":5,"messages":[{"role":"user","content":"Hi"}]}' \
    2>/dev/null)

ACTUAL_MODEL=$(echo "$RESPONSE" | jq -r '.model' 2>/dev/null)
ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error // .message' 2>/dev/null)

if [ -n "$ACTUAL_MODEL" ] && [ "$ACTUAL_MODEL" != "null" ]; then
    echo -e "${GREEN}✓${NC} API key validated successfully"
    echo "  Requested: claude-opus-4"
    echo "  Got: $ACTUAL_MODEL"

    # Check if we got the wrong model (config routing issue)
    if echo "$ACTUAL_MODEL" | grep -q "sonnet" && ! echo "$ACTUAL_MODEL" | grep -q "opus"; then
        echo ""
        echo -e "${RED}⚠ WARNING: Config Routing Issue Detected!${NC}"
        echo -e "${YELLOW}  You requested Opus but got Sonnet${NC}"
        echo ""
        echo "  This means your API key is using the wrong Portkey config."
        echo "  Expected config: 'pc-claude-60f174' (claude-code-both-live)"
        echo "  Your config: Likely 'Claude-Code' or similar"
        echo ""
        echo "  Fix this in Portkey Dashboard:"
        echo "  1. Go to: https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/"
        echo "  2. Navigate to API Keys"
        echo "  3. Find your key: ${API_KEY:0:10}..."
        echo "  4. Change assigned config to: 'pc-claude-60f174'"
        echo ""
    elif echo "$ACTUAL_MODEL" | grep -q "opus"; then
        echo -e "${GREEN}  ✓ Model routing is working correctly!${NC}"
    fi
else
    echo -e "${RED}✗${NC} API key validation failed"
    echo "  Error: $ERROR_MSG"
    echo "  Response: $RESPONSE"
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
