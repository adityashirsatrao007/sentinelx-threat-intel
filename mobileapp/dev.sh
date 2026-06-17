#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# SentinelX Mobile Dev Setup — Run this once before starting Expo
# It auto-detects your backend URL (ngrok or local IP) and patches api.js
# ─────────────────────────────────────────────────────────────────────────────

API_JS="/Users/surajbayas/Developer/SentinelX/mobileapp/src/services/api.js"

echo ""
echo "🛡️  SentinelX Mobile Dev Setup"
echo "────────────────────────────────"

# ── 1. Try ngrok local API (if ngrok is running) ──────────────────────────────
NGROK_URL=$(curl -s --max-time 2 http://localhost:4040/api/tunnels 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print([t['public_url'] for t in d['tunnels'] if t['proto']=='https'][0])" 2>/dev/null)

# ── 2. Fall back to local IP ───────────────────────────────────────────────────
if [ -z "$NGROK_URL" ]; then
  LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
  if [ -z "$LOCAL_IP" ]; then
    echo "❌ Could not detect IP. Make sure you're on Wi-Fi or Hotspot."
    exit 1
  fi
  API_URL="http://${LOCAL_IP}:8000/api/v1"
  echo "📡 Using local IP:  $API_URL"
  echo "   (For best results, start ngrok: ngrok http 8000)"
else
  API_URL="${NGROK_URL}/api/v1"
  echo "🌐 Using ngrok URL: $API_URL"
fi

# ── 3. Patch api.js ────────────────────────────────────────────────────────────
# Replace only the API_URL constant line
sed -i '' "s|const API_URL = .*|const API_URL = '${API_URL}'; // auto-set by dev.sh|" "$API_JS"

echo "✅ api.js patched!"
echo ""
echo "Next steps:"
echo "  cd mobileapp"
echo "  npx expo start -c"
echo ""
