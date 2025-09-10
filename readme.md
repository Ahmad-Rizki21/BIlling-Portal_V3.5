# Project Billing System V2

Sistem billing otomatis untuk provider internet FTTH, dibangun dengan FastAPI dan Vue.js.

---

## 🚀 Dokumentasi Lengkap

Untuk panduan teknis yang mendalam, arsitektur, dan referensi API, silakan kunjungi situs dokumentasi lengkap kami yang dibuat menggunakan Swimm.

**[Buka Dokumentasi Lengkap](https://app.swimm.io/workspaces/9UKPbEliQw5IjMXBOALl/repos/Z2l0aHViJTNBJTNBQmlsbGluZ0Z0dGhWMiUzQSUzQUFobWFkLVJpemtpMjE=/branch/main/docs/cu0bxclv)**

**[Buka Dokumentasi Lengkap API](https://artacomindo.portal.swaggerhub.com/api/docs/billing-system-api-v-1-0-0)**

---

## Teknologi yang Digunakan

* **Backend**: Python, FastAPI
* **Frontend**: Vue.js, TypeScript
* **Database**: MySQL (dengan SQLAlchemy & Alembic)
* **Otomatisasi**: Mikrotik API, Xendit API

---

## Instalasi & Setup Lokal

---

## 🚀 Setup & Deploy ke Server

Panduan ini menjelaskan langkah-langkah untuk melakukan setup proyek dari awal di server produksi (misalnya, Ubuntu).

### Prasyarat di Server
Pastikan server Anda sudah terinstal:
* Python 3.10+ & Pip
* Node.js & NPM
* Server Database (contoh ini menggunakan MySQL)
* Web Server (contoh ini menggunakan Nginx)

---
### 1. Setup Backend (FastAPI)

1.  **Clone Repositori**
    ```bash
    git clone [https://github.com/Ahmad-Rizki21/BillingFtthV2.git](https://github.com/Ahmad-Rizki21/BillingFtthV2.git)
    cd BillingFtthV2
    ```

2.  **Buat dan Aktifkan Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instal Dependensi Python**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi File `.env`**
    Salin file contoh dan isi nilainya sesuai dengan konfigurasi server Anda.
    ```bash
    cp .env.example .env
    nano .env
    ```
    * **Penting**: Sesuaikan `DATABASE_URL` dengan username, password, dan nama database di server Anda. Ganti juga semua kunci API Xendit dengan kunci mode **produksi**.

5.  **Jalankan Migrasi Database**
    Perintah ini akan membuat semua tabel yang dibutuhkan di database Anda.
    ```bash
    alembic upgrade head
    ```

---
### 2. Setup Frontend (Vue.js)

1.  **Masuk ke Folder Frontend**
    ```bash
    cd frontend
    ```

2.  **Instal Dependensi Node.js**
    ```bash
    npm install
    ```

3.  **Build Aplikasi untuk Produksi**
    Perintah ini akan membuat folder `dist` yang berisi file statis (HTML, CSS, JS) yang sudah dioptimalkan.
    ```bash
    npm run build
    ```

---
### 3. Konfigurasi Web Server (Contoh Nginx)

Nginx akan bertindak sebagai *reverse proxy*. Tugasnya adalah:
* Menyajikan file statis dari folder `frontend/dist`.
* Meneruskan semua permintaan yang diawali dengan `/api/` ke aplikasi backend FastAPI.

Buat file konfigurasi baru di `/etc/nginx/sites-available/billingsystem`:
```nginx
server {
    listen 80;
    server_name nama_domain_anda.com; # Ganti dengan domain Anda

    # Lokasi file hasil build frontend
    root /path/ke/proyek/BillingFtthV2/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Teruskan request API ke backend FastAPI
    location /api/ {
        proxy_pass [http://127.0.0.1:8000](http://127.0.0.1:8000);
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

```
### 4. Menjalankan Aplikasi Backend

Aplikasi backend perlu terus berjalan untuk melayani permintaan API.

##### Untuk Development Lokal
Perintah ini digunakan saat Anda melakukan coding di laptop. Server akan otomatis restart setiap kali ada perubahan pada kode. Jangan gunakan ini di server produksi.

```
uvicorn app.main:app --reload
```


##### Untuk Server Produksi
Di server, kita menggunakan Gunicorn sebagai manajer proses yang lebih tangguh.

```Instal Gunicorn:

pip install gunicorn
```

Jalankan Aplikasi dengan Gunicorn:
Dari direktori root proyek (BillingFtthV2), jalankan:

```
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
```

-w 4: Menjalankan 4 proses worker (sesuaikan dengan jumlah core CPU server Anda).
-k uvicorn.workers.UvicornWorker: Memberitahu Gunicorn untuk menggunakan Uvicorn.
Tips: Untuk menjaga agar Gunicorn tetap berjalan selamanya, gunakan manajer proses seperti systemd atau PM2.