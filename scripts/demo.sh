#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# AURA Demo Runner — Google AI Agent Labs Oslo 2026 · Team 6
# Usage:  ./demo.sh [scenario]
#   ./demo.sh          — interactive menu
#   ./demo.sh 1        — Happy path: buy 1 laptop (settlement confirmed)
#   ./demo.sh 2        — Buy 5 laptops (compliance + policy block)
#   ./demo.sh 3        — Blacklisted vendor (AML block)
#   ./demo.sh 4        — Geo-restricted vendor (OFAC block)
#   ./demo.sh 5        — High-value order needing approval (REVIEW)
#   ./demo.sh health   — Check API health
#   ./demo.sh start    — Start API server + dashboard
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

API="http://localhost:8080"
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
RESET='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────

banner() {
  echo ""
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo -e "${BOLD}  🌐 AURA  —  $1${RESET}"
  echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
}

run_scenario() {
  local title="$1"
  local message="$2"
  local session="$3"
  local expect="$4"

  banner "$title"
  echo -e "${YELLOW}📨 Request:${RESET}  $message"
  echo -e "${YELLOW}🔮 Expected:${RESET} $expect"
  echo ""
  echo -e "${YELLOW}⏳ Running pipeline... (Scout → Sentinel → Closer)${RESET}"
  echo ""

  RESPONSE=$(curl -s -X POST "$API/run" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"$message\", \"session_id\": \"$session\"}")

  if echo "$RESPONSE" | python3 -m json.tool > /dev/null 2>&1; then
    echo "$RESPONSE" | python3 -c "
import json, sys, textwrap
data = json.load(sys.stdin)
resp = data.get('response', data.get('message', str(data)))
# Pretty-print with word wrap
for para in resp.split('\n'):
    if para.strip():
        print(textwrap.fill(para, width=100, subsequent_indent='  ') if len(para) > 100 else para)
    else:
        print()
"
  else
    echo "$RESPONSE"
  fi

  echo ""
  echo -e "${CYAN}─────────────────────────────────────────────────────────────${RESET}"
}

check_health() {
  echo -en "  Checking API at $API/health ... "
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API/health" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Online${RESET}"
    return 0
  else
    echo -e "${RED}✗ Offline (HTTP $STATUS)${RESET}"
    return 1
  fi
}

start_services() {
  banner "Starting Services"
  AURA_DIR="$(cd "$(dirname "$0")" && pwd)"

  echo "  Starting API server on :8080 ..."
  cd "$AURA_DIR"
  AURA_PROVIDER_MODE=mock AUTH_ENABLED=false \
    nohup uvicorn main:app --port 8080 > /tmp/aura-api.log 2>&1 &
  sleep 3
  check_health

  echo ""
  echo "  Starting dashboard on :8501 ..."
  nohup streamlit run ui/dashboard.py --server.port 8501 --server.headless true \
    > /tmp/aura-dashboard.log 2>&1 &
  sleep 3
  DASH=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8501" 2>/dev/null || echo "000")
  if [ "$DASH" = "200" ]; then
    echo -e "  Dashboard ...${GREEN}✓ Online${RESET}"
  else
    echo -e "  Dashboard ...${YELLOW}Starting (check http://localhost:8501)${RESET}"
  fi

  echo ""
  echo -e "${GREEN}✓ Services started.${RESET}"
  echo -e "  API:       ${BOLD}http://localhost:8080${RESET}"
  echo -e "  Dashboard: ${BOLD}http://localhost:8501${RESET}"
  echo ""
}

menu() {
  banner "Demo Scenarios"
  echo -e "  ${BOLD}1)${RESET} 🟢 Happy path       — Buy 1 laptop (settlement confirmed)"
  echo -e "  ${BOLD}2)${RESET} 🔴 Policy block      — Buy 5 laptops (exceeds \$5K cap)"
  echo -e "  ${BOLD}3)${RESET} 🚫 AML block         — Buy from blacklisted vendor"
  echo -e "  ${BOLD}4)${RESET} 🌍 Geo-restricted    — Buy from sanctioned country vendor"
  echo -e "  ${BOLD}5)${RESET} 🔵 Approval needed   — High-value order (\$3,800) → REVIEW"
  echo -e "  ${BOLD}h)${RESET} Health check"
  echo -e "  ${BOLD}s)${RESET} Start services"
  echo -e "  ${BOLD}q)${RESET} Quit"
  echo ""
  read -rp "  Choose scenario [1-5, h, s, q]: " CHOICE
  run_choice "$CHOICE"
}

run_choice() {
  case "$1" in
    1)
      run_scenario \
        "Scenario 1 — Happy Path: Buy 1 Laptop" \
        "Procure 1 unit of Laptop Pro 15 from the best available vendor, budget USD 2000" \
        "demo-happy-$(date +%s)" \
        "SETTLEMENT_CONFIRMED with mandate ID and discount summary"
      ;;
    2)
      run_scenario \
        "Scenario 2 — Policy Block: Buy 5 Laptops" \
        "Procure 5 units of Laptop Pro 15 from the best available vendor, budget USD 8000" \
        "demo-policy-$(date +%s)" \
        "PAYMENT_ABORTED — all vendors exceed the \$5,000 AP2 mandate cap"
      ;;
    3)
      run_scenario \
        "Scenario 3 — AML Block: Blacklisted Vendor" \
        "Procure 2 laptops from ShadowHardware, budget USD 3000" \
        "demo-aml-$(date +%s)" \
        "PAYMENT_ABORTED — ShadowHardware is on the AML blacklist (country code XX)"
      ;;
    4)
      run_scenario \
        "Scenario 4 — Geo-Restriction: Sanctioned Country" \
        "Purchase 10 units of office equipment from IranTech Supplies, budget USD 2000" \
        "demo-geo-$(date +%s)" \
        "POLICY_BLOCKED — vendor country code IR is on the OFAC sanctions list"
      ;;
    5)
      run_scenario \
        "Scenario 5 — Approval Required: High-Value Order" \
        "Procure 3 TechCorp Nordic laptop servers for the data centre, budget USD 3800" \
        "demo-review-$(date +%s)" \
        "PAYMENT_PENDING_REVIEW — order requires manager approval (>\$2,000 threshold)"
      ;;
    health|h)
      echo ""
      check_health
      echo ""
      ;;
    start|s)
      start_services
      ;;
    q|quit|exit)
      echo -e "\n  ${GREEN}Good luck with the demo! 🚀${RESET}\n"
      exit 0
      ;;
    *)
      echo -e "\n  ${RED}Unknown option: $1${RESET}\n"
      ;;
  esac
}

# ── Main ──────────────────────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}  ██████████████████████████████████████████${RESET}"
echo -e "${CYAN}  ██  AURA — Autonomous Reliable Commerce  ██${RESET}"
echo -e "${CYAN}  ██  Google AI Agent Labs Oslo 2026 · T6  ██${RESET}"
echo -e "${CYAN}  ██████████████████████████████████████████${RESET}"

if ! check_health 2>/dev/null; then
  echo -e "  ${YELLOW}⚠  API not running. Use './demo.sh start' or './demo.sh s' to start services.${RESET}"
fi

if [ $# -gt 0 ]; then
  run_choice "$1"
else
  while true; do
    menu
  done
fi
