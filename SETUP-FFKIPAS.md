# Setup FreeFire-Api untuk FFKIPAS (Opsi A)

Sudah diisi guest valid kamu + OB55.

## Guest terpasang
- UID: `8037655362`
- Region guest: **BD**
- Password: sudah di `Configuration/AccountConfiguration.json`

## Install & jalanin

```bash
cd FreeFire-Api-ffkipas
pip install -r requirements.txt
python app.py
```

Tes di browser:
```
http://127.0.0.1:5000/get_player_personal_show?server=BD&uid=1704140050
```

**Penting:** `server=BD` = region **guest**, bukan region UID yang dicek.

Kalau sukses → JSON berisi profile + **clothes** (ID skin) + skills.

## Endpoint
| Endpoint | Contoh |
|----------|--------|
| Personal show (skin dll) | `/get_player_personal_show?server=BD&uid=UID` |
| Stats | `/get_player_stats?server=BD&uid=UID&gamemode=br` |

## Kalau error Authentication failed
1. Tes JWT masih hidup:
   `https://jwt-ob55-api.onrender.com/token?uid=8037655362&password=PASSWORD`
2. Di `Api/Account.py` ganti MajorLogin ke salah satu:
   - `https://loginbp.ppmainecoonghj.com/MajorLogin` (sudah diset)
   - `https://loginbp.ggpolarbear.com/MajorLogin`
   - `https://loginbp.ggblueshark.com/MajorLogin`
3. Pastikan `RELEASEVERSION = "OB55"` di `Configuration/APIConfiguration.py`

## Deploy
Railway / VPS:
```bash
gunicorn -b 0.0.0.0:$PORT app:app
```

## Sambung web FFKIPAS
Ganti fetch cek akun ke:
```
https://DOMAIN-API-KAMU/get_player_personal_show?server=BD&uid=
```
Lalu mapping field clothes / equipedSkills ke UI skin.

## Keamanan
Jangan push `AccountConfiguration.json` ke GitHub **publik**.
