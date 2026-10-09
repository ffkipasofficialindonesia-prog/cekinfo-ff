import requests
import Proto.compiled.MajorLogin_pb2
from Utilities.until import encode_protobuf, decode_protobuf
import json
from Configuration.APIConfiguration import RELEASEVERSION, DEBUG


def get_garena_token(uid, password):
    """
    Get Garena token using uid and password
    
    Args:
        uid (str): User ID
        password (str): Password
    
    Returns:
        dict: JSON response from the API
    """
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"

    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }

    headers = {
        'User-Agent': "GarenaMSDK/4.0.19P9(A063 ;Android 13;en;IN;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        if DEBUG:
            print("[oauth/guest/token/grant] Response(raw):", response.content, "\n")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None



def get_major_login(logintoken, openid):
    """
    Perform major login with the provided credentials
    
    Args:
        logintoken (str): The login token
        openid (str): The open ID
    
    Returns:
        dict: JSON response from the login API
    """
    # Create encrypted payload
    encrypted_payload = encode_protobuf({
        "openid": openid,
        "logintoken": logintoken,
        "platform": "4",
    }, Proto.compiled.MajorLogin_pb2.request())

    # API endpoint
    # url = "https://loginbp.ggblueshark.com/MajorLogin"
    url = "https://loginbp.ppmainecoonghj.com/MajorLogin"

    # Headers
    headers = {
        'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip",
        'Content-Type': "application/octet-stream",
        'Expect': "100-continue",
        'Authorization': "Bearer",
        'X-Unity-Version': "2018.4.11f1",
        'X-GA': "v1 1",
        'ReleaseVersion': RELEASEVERSION,
        'Content-Type': "application/x-www-form-urlencoded"
    }

    # Make the request
    response = requests.post(url, data=encrypted_payload, headers=headers)
    if DEBUG:
        print("[MajorLogin] Response(raw):", response.content, "\n")
    try:
        # Decode and return the response as JSON
        message = decode_protobuf(response.content, Proto.compiled.MajorLogin_pb2.response)
        return message
    except:
        print("[MajorLogin] Error:", response.text)
    return False



def _jwt_exp(token):
    """Ambil exp dari payload JWT (unix). 0 kalau gagal parse."""
    try:
        import base64, json
        part = token.split(".")[1]
        part += "=" * (-len(part) % 4)
        payload = json.loads(base64.urlsafe_b64decode(part.encode("utf-8")))
        return int(payload.get("exp") or 0)
    except Exception:
        return 0


def get_login_via_jwt_provider(uid, password, region="BD"):
    """
    Auto JWT — prioritas:
    1) Env JWT_TOKEN kalau belum expired (sisa > 3 menit)
    2) Cache file /tmp atau lokal
    3) Auto-fetch dari JWT provider pakai guest uid+password
       → tidak perlu ganti JWT manual tiap jam (asal provider hidup)
    """
    import os, json, time
    from pathlib import Path
    import requests
    from Configuration.APIConfiguration import REGION_URLS, JWT_PROVIDER, DEBUG

    urls = REGION_URLS.get(str(region).upper()) or REGION_URLS.get("OTHERS") or REGION_URLS["BD"]
    server_url = urls["client_url"].rstrip("/")
    now = time.time()
    skew = 180  # refresh 3 menit sebelum exp

    def ok_token(tok):
        if not tok or not str(tok).startswith("eyJ"):
            return False
        exp = _jwt_exp(tok)
        if exp <= 0:
            return True  # tidak bisa baca exp → anggap masih dipakai
        return exp > (now + skew)

    def pack(tok, reg=None, extra=None):
        d = {
            "token": tok,
            "serverUrl": server_url,
            "region": reg or region,
        }
        if extra:
            d.update(extra)
        return d

    # 1) Env JWT_TOKEN (hanya jika masih valid)
    env_tok = (os.environ.get("JWT_TOKEN") or "").strip()
    if ok_token(env_tok):
        if DEBUG:
            print("[JWT] env hit, exp=", _jwt_exp(env_tok))
        return pack(env_tok, extra={"from_env": True})

    # 2) Cache (lokal + /tmp untuk Vercel)
    for cache_path in (
        Path(__file__).resolve().parent.parent / "jwt_cache.json",
        Path("/tmp/jwt_cache.json"),
    ):
        try:
            if not cache_path.exists():
                continue
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            token = cached.get("token") or cached.get("Jwt_Token")
            exp_file = float(cached.get("expires_at") or 0)
            if token and ok_token(token) and (exp_file <= 0 or exp_file > now):
                if DEBUG:
                    print("[JWT] cache hit", cache_path)
                return pack(
                    token,
                    reg=cached.get("region") or region,
                    extra={"account_uid": cached.get("account_uid"), "from_cache": True},
                )
        except Exception as e:
            if DEBUG:
                print("[JWT] cache fail", e)

    # 3) Auto-fetch dari provider (inti: biar tidak manual tiap jam)
    guest_uid = str(uid or os.environ.get("FF_GUEST_UID") or "").strip()
    guest_pw = str(password or os.environ.get("FF_GUEST_PASSWORD") or "").strip()
    if not guest_uid or not guest_pw:
        if DEBUG:
            print("[JWT] no guest credentials for auto-refresh")
        return False

    last_err = None
    for attempt in range(1, 4):
        try:
            if DEBUG:
                print(f"[JWT provider] auto-refresh attempt {attempt} ...")
            r = requests.get(
                f"{JWT_PROVIDER}?uid={guest_uid}&password={guest_pw}",
                headers={"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13)"},
                timeout=55,
            )
            data = r.json()
            token = data.get("Jwt_Token") or data.get("token") or data.get("jwt")
            if not token:
                last_err = data
                time.sleep(2)
                continue
            exp = _jwt_exp(token) or (now + 3300)
            payload = {
                "token": token,
                "serverUrl": server_url,
                "region": data.get("Region") or region,
                "account_uid": data.get("Account_uid"),
                "expires_at": exp,
            }
            for cache_path in (
                Path("/tmp/jwt_cache.json"),
                Path(__file__).resolve().parent.parent / "jwt_cache.json",
            ):
                try:
                    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                except Exception:
                    pass
            if DEBUG:
                print("[JWT] auto-refresh OK exp=", exp)
            return pack(
                token,
                reg=payload["region"],
                extra={"account_uid": payload["account_uid"], "from_cache": False, "auto_refresh": True},
            )
        except Exception as e:
            last_err = str(e)
            if DEBUG:
                print("[JWT provider] exception:", e)
            time.sleep(2 * attempt)

    if DEBUG:
        print("[JWT provider] failed:", last_err)
    # fallback terakhir: env token meskipun hampir/expired (lebih baik dari mati total)
    if env_tok.startswith("eyJ"):
        return pack(env_tok, extra={"from_env": True, "stale": True})
    return False


def save_jwt_manual(token, region="BD", server_url=None):
    """Simpan JWT manual ke jwt_cache.json (kalau provider timeout)."""
    import json, time
    from pathlib import Path
    from Configuration.APIConfiguration import REGION_URLS
    urls = REGION_URLS.get(str(region).upper()) or REGION_URLS["BD"]
    server_url = (server_url or urls["client_url"]).rstrip("/")
    cache_path = Path(__file__).resolve().parent.parent / "jwt_cache.json"
    payload = {
        "token": token.strip(),
        "serverUrl": server_url,
        "region": region,
        "expires_at": time.time() + 3300,
        "manual": True,
    }
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
