# Deploy FF API ke GitHub + Vercel

## 1. Persiapan GitHub

1. Buat repo **baru** di GitHub (disarankan **Private**).
2. Di folder `FreeFire-Api-ffkipas`:

```bash
# pastikan secret tidak ikut
# cek .gitignore sudah ada

git init
git add .
git status
# PASTIKAN tidak ada: AccountConfiguration.json, jwt_cache.json, password

git commit -m "FF info API"
git branch -M main
git remote add origin https://github.com/USERNAME/NAMA-REPO.git
git push -u origin main
```

**Jangan push:** `AccountConfiguration.json`, `jwt_cache.json`, password guest.

## 2. Deploy Vercel

1. Buka [vercel.com](https://vercel.com) → Login dengan GitHub  
2. **Add New Project** → pilih repo tadi  
3. Framework: Other / Python  
4. **Environment Variables** (wajib):

| Name | Value |
|------|--------|
| `FF_GUEST_UID` | `8037655362` |
| `FF_GUEST_PASSWORD` | password guest kamu |
| `FF_REGION` | `BD` |
| `JWT_TOKEN` | (opsional) tempel `eyJ...` yang baru |

5. Deploy

## 3. Tes link publik

Setelah deploy, URL contoh:
```
https://nama-project.vercel.app/get_player_personal_show?server=BD&uid=1704140050
```

Cache JWT manual (kalau perlu):
```
https://nama-project.vercel.app/cache_jwt?token=eyJ...&region=BD
```
Catatan: di Vercel file cache **tidak permanen** (serverless). Lebih andal isi **JWT_TOKEN** di Environment Variables, update manual tiap ~1 jam.

## 4. Sambung ke web FFKIPAS

Di `script.js`, ganti URL cek akun ke:
```
https://nama-project.vercel.app/get_player_personal_show?server=BD&uid=
```

## 5. Batasan Vercel

| Hal | Keterangan |
|-----|------------|
| Timeout | ~10–60 detik (plan) — JWT provider lambat bisa gagal |
| JWT cache file | Tidak awet → pakai env `JWT_TOKEN` |
| Cold start | Request pertama lebih lama |

Kalau sering timeout, lebih stabil pakai **Railway** (bukan serverless).
