# Panduan Deployment Docker (Billing Portal FTTH)

Dokumen ini menjelaskan cara menjalankan sistem billing menggunakan Docker untuk mempermudah proses deployment dan standarisasi environment.

---

## 🏗️ Struktur Docker

Proyek ini menggunakan 3 container utama:

1.  **billing-db**: Database MySQL 8.0.
2.  **billing-backend**: FastAPI server (Port 8000).
3.  **billing-frontend**: Vue.js app dilayani oleh Nginx (Port 80).

---

## 🚀 Cara Menjalankan (Local Development)

Pastikan Docker Desktop sudah terinstal, lalu jalankan:

```bash
docker-compose up --build -d
```

Sistem akan tersedia di:

- **Frontend**: `http://localhost`
- **Backend API**: `http://localhost:8000`
- **Dokumentasi API**: `http://localhost:8000/docs`

---

## ☁️ Deployment ke Server (CI/CD)

Proyek ini sudah dilengkapi dengan **GitHub Actions** (`.github/workflows/deploy-docker.yml`).

### Alur Kerja:

1.  Setiap Anda melakukan `git push` ke branch `main` atau `dev`, GitHub akan otomatis membangun Docker Image.
2.  Image akan di-push ke **GitHub Container Registry (GHCR)**.
3.  Di server tujuan, Anda cukup menarik image terbaru dan menjalankannya.

### Langkah di Server Production:

1.  Salin file `docker-compose.yml` ke server.
2.  Ganti build context dengan image dari registry (opsional, jika ingin menggunakan image yang sudah di-build oleh CI).
3.  Jalankan:
    ```bash
    docker-compose pull
    docker-compose up -d
    ```

---

## 🛠️ Konfigurasi Environment

Variabel lingkungan utama diatur di dalam `docker-compose.yml` pada bagian `environment`. Pastikan untuk mengubah:

- `MYSQL_ROOT_PASSWORD`
- `DATABASE_URL` (sesuaikan user:pass@host)
- `SECRET_KEY` (gunakan kunci yang kuat untuk enkripsi token JWT)
- `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID` (untuk notifikasi monitoring)

---

## 🔍 Log & Monitoring

Untuk melihat log dari semua container:

```bash
docker-compose logs -f
```

Untuk masuk ke dalam terminal backend:

```bash
docker exec -it billing-backend bash
```
