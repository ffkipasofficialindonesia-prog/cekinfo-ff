"""Ambil JWT dari provider lalu simpan ke jwt_cache.json — jalankan saat provider lagi hidup."""
import json, time, requests
from pathlib import Path

UID = "8037655362"
PASSWORD = "798B716932804B2150D8CFA7B2D68DF6771AF56582A15107A7220B31C989755D"
PROVIDER = "https://jwt-ob55-api.onrender.com/token"
CLIENT = "https://clientbp.ppmainecoonghj.com"

print("Request JWT (bisa 1-2 menit kalau cold start)...")
r = requests.get(f"{PROVIDER}?uid={UID}&password={PASSWORD}", timeout=120)
data = r.json()
token = data.get("Jwt_Token") or data.get("token")
if not token:
    print("GAGAL:", data)
    raise SystemExit(1)

payload = {
    "token": token,
    "serverUrl": CLIENT,
    "region": data.get("Region") or "BD",
    "account_uid": data.get("Account_uid"),
    "expires_at": time.time() + 3300,
    "raw": data,
}
Path("jwt_cache.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("OK tersimpan jwt_cache.json")
print("Region:", payload["region"])
print("Token length:", len(token))
print("Sekarang jalankan: python app.py")
print("Lalu buka: /get_player_personal_show?server=BD&uid=UID_TARGET")
