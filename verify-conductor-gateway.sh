#!/bin/bash
# Copyright Epic Games, Inc. All Rights Reserved.
#
# Conductor Gateway Configuration Verification Script
# This script helps verify that Conductor is properly configured to use the Epic Claude Gateway

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GATEWAY_URL="https://live.ai.epicgames.com"
PORTKEY_CONFIG="pc-claude-60f174"
CONDUCTOR_DB="$HOME/Library/Application Support/com.conductor.app/conductor.db"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Conductor + Epic Gateway Configuration Verifier${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Function to check status
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check 1: Conductor installed
echo -e "\n${BLUE}[1/7]${NC} Checking Conductor installation..."
if [ -d "/Applications/Conductor.app" ]; then
    check_pass "Conductor app found"
    CONDUCTOR_VERSION=$(defaults read /Applications/Conductor.app/Contents/Info.plist CFBundleShortVersionString 2>/dev/null || echo "unknown")
    check_info "Version: $CONDUCTOR_VERSION"
else
    check_fail "Conductor app not found at /Applications/Conductor.app"
    echo "  → Download from: https://www.conductor.build/"
    exit 1
fi

# Check 2: Claude Code bundled
echo -e "\n${BLUE}[2/7]${NC} Checking bundled Claude Code..."
CLAUDE_PATH="/Applications/Conductor.app/Contents/Resources/bin/claude"
if [ -f "$CLAUDE_PATH" ]; then
    check_pass "Bundled Claude Code found"
else
    check_fail "Claude Code binary not found at expected location"
fi

# Check 3: Gateway connectivity
echo -e "\n${BLUE}[3/7]${NC} Testing gateway connectivity..."
if curl -s -I --max-time 5 "$GATEWAY_URL" > /dev/null 2>&1; then
    check_pass "Gateway is reachable: $GATEWAY_URL"
else
    check_fail "Cannot reach gateway: $GATEWAY_URL"
    check_warn "You may need to be on Epic's VPN"
fi

# Check 4: Conductor database
echo -e "\n${BLUE}[4/7]${NC} Checking Conductor database..."
if [ -f "$CONDUCTOR_DB" ]; then
    check_pass "Conductor database found"

    # Try to read settings (requires sqlite3)
    if command -v sqlite3 &> /dev/null; then
        # Check for gateway URL in settings
        GATEWAY_IN_DB=$(sqlite3 "$CONDUCTOR_DB" "SELECT value FROM settings WHERE key='anthropic_base_url';" 2>/dev/null || echo "")
        if [ -n "$GATEWAY_IN_DB" ]; then
            if [ "$GATEWAY_IN_DB" = "$GATEWAY_URL" ]; then
                check_pass "Gateway URL configured in database"
            else
                check_warn "Different gateway URL in database: $GATEWAY_IN_DB"
            fi
        else
            check_info "No gateway URL found in database (will check env vars)"
        fi
    else
        check_warn "sqlite3 not available - cannot inspect database"
    fi
else
    check_warn "Conductor database not found (may not have been run yet)"
fi

# Check 5: Portkey API key
echo -e "\n${BLUE}[5/7]${NC} Checking Portkey configuration..."
echo -n "Do you have a Portkey API key? (y/n): "
read -r HAS_API_KEY

if [ "$HAS_API_KEY" = "y" ] || [ "$HAS_API_KEY" = "Y" ]; then
    check_pass "User confirmed having Portkey API key"

    echo -n "Enter your API key to validate (or press Enter to skip): "
    read -rs API_KEY
    echo ""

    if [ -n "$API_KEY" ]; then
        # Test the API key with Opus request to check routing
        echo "  Testing API key and config routing..."
        RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" --max-time 10 \
            -X POST "$GATEWAY_URL/v1/messages" \
            -H "Content-Type: application/json" \
            -H "x-portkey-api-key: $API_KEY" \
            -H "x-portkey-debug: true" \
            -H "anthropic-version: 2023-06-01" \
            -d '{"model":"claude-opus-4","max_tokens":5,"messages":[{"role":"user","content":"Hi"}]}' \
            2>/dev/null)

        HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
        BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")
        ACTUAL_MODEL=$(echo "$BODY" | grep -o '"model":"[^"]*"' | cut -d'"' -f4)

        if [ "$HTTP_CODE" = "200" ]; then
            check_pass "API key validated successfully"

            # Check for config routing issue
            if echo "$ACTUAL_MODEL" | grep -q "sonnet" && ! echo "$ACTUAL_MODEL" | grep -q "opus"; then
                check_warn "Model routing issue detected!"
                echo "  → Requested: claude-opus-4"
                echo "  → Got: $ACTUAL_MODEL"
                echo ""
                check_warn "Your API key is using the wrong Portkey config"
                echo "  → Expected config: pc-claude-60f174"
                echo "  → Your config: Likely 'Claude-Code' or similar"
                echo ""
                echo "  Fix this in Portkey Dashboard:"
                echo "  1. Go to API Keys section"
                echo "  2. Find your key: ${API_KEY:0:10}..."
                echo "  3. Change assigned config to: pc-claude-60f174"
                echo ""
            elif echo "$ACTUAL_MODEL" | grep -q "opus"; then
                check_pass "Model routing works correctly (got Opus as expected)"
            fi
        elif [ "$HTTP_CODE" = "401" ]; then
            check_fail "API key is invalid or expired"
        elif [ "$HTTP_CODE" = "403" ]; then
            check_fail "API key doesn't have required permissions"
        else
            check_warn "Validation inconclusive (HTTP $HTTP_CODE)"
        fi
    else
        check_info "API key validation skipped"
    fi
else
    check_fail "Portkey API key required"
    echo "  → Get API key from: https://app.portkey.ai/organisation/61d0748c-aba9-4b7c-bf18-008150ba9545/getting-started"
    exit 1
fi

# Check 6: Environment variables (if Conductor is running)
echo -e "\n${BLUE}[6/7]${NC} Checking environment variables..."
if pgrep -x "Conductor" > /dev/null; then
    check_info "Conductor is currently running"
    check_warn "Restart Conductor after changing environment variables"
else
    check_info "Conductor is not running"
fi

# Check 7: Configuration summary
echo -e "\n${BLUE}[7/7]${NC} Configuration summary..."
echo ""
echo "Required environment variables for Conductor Settings → Env:"
echo ""
echo -e "${GREEN}ANTHROPIC_BASE_URL${NC}=${GATEWAY_URL}"
echo -e "${GREEN}ANTHROPIC_AUTH_TOKEN${NC}=test"
echo -e "${GREEN}ANTHROPIC_CUSTOM_HEADERS${NC}=x-portkey-api-key: YOUR_API_KEY_HERE"
echo "x-portkey-debug: true"
echo "x-vertex-ai-llm-request-type: shared"
echo ""
echo -e "${YELLOW}Note: Do NOT include x-portkey-config header - your API key has a default config${NC}"
echo ""

# Final recommendations
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Recommendations${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

echo "Next steps:"
echo "  1. Open Conductor → Settings → Env"
echo "  2. Add the environment variables shown above"
echo "  3. Replace YOUR_API_KEY_HERE with your actual key"
echo "  4. Restart Conductor"
echo "  5. Create a new workspace and test"
echo ""

echo "Documentation:"
echo "  • Full Guide: CONDUCTOR_SETUP.md"
echo "  • Quick Reference: CONDUCTOR_QUICK_REFERENCE.md"
echo ""

echo "Support:"
echo "  • Epic Gateway: Slack #ts-ai-gateway-support"
echo "  • Conductor: https://github.com/conductor-build/conductor/issues"
echo ""

echo -e "${GREEN}Verification complete!${NC}"
