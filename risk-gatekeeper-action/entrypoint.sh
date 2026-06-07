#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────
#  Sentinel.AI Risk Gatekeeper – entrypoint.sh
#  Queries the Sentinel.AI FastAPI backend for
#  a pre-deployment risk assessment.
# ─────────────────────────────────────────────

SENTINEL_URL="${SENTINEL_URL:-http://localhost:8000}"
API_KEY="${SENTINEL_API_KEY}"
SERVICE="${SENTINEL_SERVICE}"
ENVIRONMENT="${SENTINEL_ENVIRONMENT:-production}"
CHANGE_TYPE="${SENTINEL_CHANGE_TYPE:-code-deploy}"
THRESHOLD="${SENTINEL_RISK_THRESHOLD:-70}"

echo "╔══════════════════════════════════════════╗"
echo "║       Sentinel.AI Risk Gatekeeper        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Service     : $SERVICE"
echo "  Environment : $ENVIRONMENT"
echo "  Change Type : $CHANGE_TYPE"
echo "  Backend URL : $SENTINEL_URL"
echo "  Threshold   : $THRESHOLD / 100"
echo ""

# ── Build request payload ────────────────────
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
PAYLOAD=$(cat <<EOF
{
  "service": "$SERVICE",
  "environment": "$ENVIRONMENT",
  "change_type": "$CHANGE_TYPE",
  "timestamp": "$TIMESTAMP",
  "deployed_by": "${GITHUB_ACTOR:-github-actions}"
}
EOF
)

echo "→ Querying Sentinel.AI agent..."

# ── Call backend ─────────────────────────────
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${SENTINEL_URL}/api/v1/deploy/analyze" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -d "$PAYLOAD" \
  --max-time 30 \
  --retry 2 \
  --retry-delay 3)

HTTP_BODY=$(echo "$RESPONSE" | head -n -1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" -ne 200 ] && [ "$HTTP_CODE" -ne 201 ]; then
  echo ""
  echo "✗ Sentinel.AI returned HTTP $HTTP_CODE"
  echo "  Body: $HTTP_BODY"
  echo ""
  echo "  Could not reach Sentinel.AI backend. Failing pipeline for safety."
  exit 1
fi

echo "✓ Response received (HTTP $HTTP_CODE)"

# ── Parse response ───────────────────────────
# RiskAnalysis returns risk_score (0–100), risk_level, recommendation
RISK_SCORE=$(echo "$HTTP_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('risk_score', 100))" 2>/dev/null || echo "100")
RISK_LEVEL=$(echo "$HTTP_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('risk_level', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
RECOMMENDATION=$(echo "$HTTP_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('recommendation', 'No recommendation available.'))" 2>/dev/null || echo "No recommendation available.")

# ── Set GitHub Actions outputs ───────────────
echo "risk-score=${RISK_SCORE}" >> "$GITHUB_OUTPUT"
echo "risk-level=${RISK_LEVEL}" >> "$GITHUB_OUTPUT"
echo "recommendation=${RECOMMENDATION}" >> "$GITHUB_OUTPUT"

# ── Print result ─────────────────────────────
echo ""
echo "┌─ Risk Assessment ──────────────────────"
echo "│  Score        : ${RISK_SCORE} / 100"
echo "│  Level        : ${RISK_LEVEL}"
echo "│  Threshold    : ${THRESHOLD} / 100"
echo "│"
echo "│  Recommendation:"
echo "│  ${RECOMMENDATION}"
echo "└────────────────────────────────────────"
echo ""

# ── Gate decision ────────────────────────────
SHOULD_BLOCK=$(python3 -c "print('yes' if float('${RISK_SCORE}') > float('${THRESHOLD}') else 'no')" 2>/dev/null || echo "yes")

if [ "$SHOULD_BLOCK" = "yes" ]; then
  echo "::error title=Sentinel.AI Risk Gate FAILED::Risk score ${RISK_SCORE} exceeds threshold ${THRESHOLD}. Deployment blocked."
  echo ""
  echo "  ✗ DEPLOYMENT BLOCKED"
  echo "  The risk score (${RISK_SCORE}) exceeds your configured threshold (${THRESHOLD})."
  echo "  Review the Sentinel.AI dashboard for details."
  exit 1
else
  echo "  ✓ DEPLOYMENT APPROVED"
  echo "  Risk score ${RISK_SCORE} is within acceptable threshold (${THRESHOLD})."
  echo "  Proceeding with deployment."
fi
