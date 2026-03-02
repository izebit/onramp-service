#!/usr/bin/env bash
# Get quote, create order, and register webhook for the onramp + webhook services.
# Requires: curl, openssl, python3 (only for pretty-print JSON; JWT is built with openssl).
# Usage:
#   ./scripts/onramp-demo.sh                    # use defaults
#   ./scripts/onramp-demo.sh get-quote
#   ./scripts/onramp-demo.sh create-order
#   ./scripts/onramp-demo.sh set-webhook [url]   # register webhook URL (default https://example.com/webhook)
#   ./scripts/onramp-demo.sh all [webhook_url]   # run get-quote, create-order, set-webhook

set -e

ONRAMP_URL="${ONRAMP_URL:-http://localhost:8000}"
WEBHOOK_URL="${WEBHOOK_URL:-http://localhost:8001}"
SECRET_KEY="${SECRET_KEY:-change-me-in-production-min-32-bytes!!}"
CLIENT_REF="${CLIENT_REF:-demo-client}"
IDEMPOTENCY_KEY="${IDEMPOTENCY_KEY:-demo-idem-$(date +%s)}"

# Base64url encode (no padding); input as first argument or stdin
base64url() {
  if [ -n "${1+x}" ]; then
    printf '%s' "$1" | base64 | tr -d '\n' | tr '+/' '-_' | tr -d '='
  else
    base64 | tr -d '\n' | tr '+/' '-_' | tr -d '='
  fi
}

# Generate a JWT valid for 1 hour (HS256, same secret as server)
get_jwt() {
  local header='{"alg":"HS256","typ":"JWT"}'
  local exp=$(($(date +%s) + 3600))
  local payload
  payload=$(printf '{"client_ref":"%s","expiration_at":%s}' "$(echo -n "$CLIENT_REF" | sed 's/\\/\\\\/g; s/"/\\"/g')" "$exp")
  local b64_header b64_payload sign_input sig_b64
  b64_header=$(base64url "$header")
  b64_payload=$(base64url "$payload")
  sign_input="${b64_header}.${b64_payload}"
  sig_b64=$(printf '%s' "$sign_input" | openssl dgst -sha256 -hmac "$SECRET_KEY" -binary | base64url)
  echo "${sign_input}.${sig_b64}"
}

# 1. Get quote from onramp (USD -> EUR, amount 1000)
get_quote() {
  echo "=== Get quote (POST $ONRAMP_URL/api/v1/quotes/USD/EUR) ==="
  QUOTE_JSON=$(curl -s -X POST "$ONRAMP_URL/api/v1/quotes/USD/EUR" \
    -H "Content-Type: application/json" \
    -d '{"amount": 5000}')
  echo "$QUOTE_JSON" | python3 -m json.tool
  export QUOTE_JSON
}

# 2. Create order on onramp (uses QUOTE_JSON from get_quote)
create_order() {
  if [ -z "${QUOTE_JSON+x}" ]; then
    echo "Getting quote first..."
    get_quote
  fi
  echo "=== Create order (POST $ONRAMP_URL/api/v1/orders) ==="
  JWT=$(get_jwt)
  RESP=$(curl -s -w "\n%{http_code}" -X POST "$ONRAMP_URL/api/v1/orders" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT" \
    -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
    -d "{\"quote\": $QUOTE_JSON}")
  BODY=$(echo "$RESP" | sed '$d')
  CODE=$(echo "$RESP" | tail -n 1)
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
  if [ "$CODE" -ne 200 ]; then
    echo "HTTP $CODE"
    return 1
  fi
  export ORDER_ID
  ORDER_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('order_id',''))")
  echo "Order ID: $ORDER_ID"
}

# 3. Register webhook for client (webhook service)
set_webhook() {
  local url="${1:-https://example.com/webhook}"
  local secret="${WEBHOOK_SIGNATURE_SECRET:-my-signature-secret}"
  echo "=== Register webhook (POST $WEBHOOK_URL/api/v1/clients/webhooks) ==="
  JWT=$(get_jwt)
  RESP=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL/api/v1/clients/webhooks" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $JWT" \
    -d "{\"url\": \"$url\", \"signature_secret\": \"$secret\"}")
  BODY=$(echo "$RESP" | sed '$d')
  CODE=$(echo "$RESP" | tail -n 1)
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
  if [ "$CODE" -ne 200 ]; then
    echo "HTTP $CODE"
    return 1
  fi
  echo "Webhook registered: $url"
}

cmd="${1:-all}"
shift || true

case "$cmd" in
  get-quote)
    get_quote
    ;;
  create-order)
    create_order
    ;;
  set-webhook)
    set_webhook "$@"
    ;;
  all)
    get_quote
    create_order
    set_webhook "${1:-https://example.com/webhook}"
    ;;
  *)
    echo "Usage: $0 {get-quote|create-order|set-webhook [url]|all [webhook_url]}"
    exit 1
    ;;
esac
