# 📋 Deployment Checklist - Traffic Monitoring System

## 🎯 Overview
Guide untuk deploy Traffic Monitoring System ke production server menggunakan WinSCP.

## 🔧 File-File yang Perlu Diupload

### **1. Backend Files (Copy ke server)**
```
app/
├── models/
│   └── traffic_history.py                          # ✅ NEW
├── services/
│   └── traffic_monitoring_service.py               # ✅ NEW
├── routers/
│   └── traffic_monitoring.py                      # ✅ NEW
├── jobs_traffic.py                               # ✅ NEW
├── main.py                                       # ✅ MODIFIED
├── config.py                                     # ✅ MODIFIED
└── models/
    ├── __init__.py                               # ✅ MODIFIED
    ├── data_teknis.py                            # ✅ MODIFIED
    └── mikrotik_server.py                        # ✅ MODIFIED
```

### **2. Frontend Files (Copy ke server)**
```
frontend/
├── src/
│   ├── services/
│   │   └── trafficMonitoringAPI.ts              # ✅ NEW
│   ├── views/
│   │   └── TrafficMonitoringView.vue             # ✅ NEW
│   ├── router/
│   │   └── index.ts                              # ✅ MODIFIED
│   └── layouts/
│       └── DefaultLayout.vue                     # ✅ MODIFIED
```

### **3. Database Files**
```
alembic/
└── versions/
    └── 3831ff243dec_add_traffic_history_table_for_pppoe_.py  # ✅ NEW
```

## 📝 Step-by-Step Deployment dengan WinSCP

### **Phase 1: Backup Existing Files**
```bash
# 1. Connect ke server dengan WinSCP
# 2. Backup critical files:
- app/main.py → app/main.py.backup
- app/config.py → app/config.py.backup
- alembic/versions/ → alembic/versions_backup/
```

### **Phase 2: Upload New Files**
```bash
# 1. Upload file backend:
- app/models/traffic_history.py
- app/services/traffic_monitoring_service.py
- app/routers/traffic_monitoring.py
- app/jobs_traffic.py

# 2. Update existing files:
- app/main.py (replace dengan yang baru)
- app/config.py (replace dengan yang baru)
- app/models/__init__.py (replace dengan yang baru)
- app/models/data_teknis.py (replace dengan yang baru)
- app/models/mikrotik_server.py (replace dengan yang baru)

# 3. Upload file frontend:
- frontend/src/services/trafficMonitoringAPI.ts
- frontend/src/views/TrafficMonitoringView.vue
- frontend/src/router/index.ts (replace dengan yang baru)
- frontend/src/layouts/DefaultLayout.vue (replace dengan yang baru)

# 4. Upload database migration:
- alembic/versions/3831ff243dec_add_traffic_history_table_for_pppoe_.py
```

### **Phase 3: Database Migration**
```bash
# SSH ke server
cd /path/to/your/app

# Activate virtual environment
source venv/bin/activate

# Run database migration
alembic upgrade head

# Verify table created
mysql -u username -p database_name -e "DESCRIBE traffic_history;"
```

### **Phase 4: Install Dependencies**
```bash
# Install any new dependencies (jika ada)
pip install -r requirements.txt

# Verify all imports work
python -c "import app.services.traffic_monitoring_service; print('✅ OK')"
```

### **Phase 5: Restart Application**
```bash
# Stop current application
pkill -f uvicorn

# Start application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Atau gunakan systemctl jika ada:
sudo systemctl restart your-app-name
```

### **Phase 6: Add Permissions**
```bash
# Connect ke database dan jalankan SQL ini:
INSERT INTO permissions (name, description, created_at) VALUES
('view_traffic_monitoring', 'View Traffic Monitoring Dashboard', NOW())
ON DUPLICATE KEY UPDATE description = 'View Traffic Monitoring Dashboard';

# Assign ke role Admin
INSERT INTO role_has_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'Admin' AND p.name = 'view_traffic_monitoring'
ON DUPLICATE KEY UPDATE role_id = VALUES(role_id);

# Assign ke role Direktur
INSERT INTO role_has_permissions (role_id, permission_id)
SELECT r.id, p.id FROM roles r, permissions p
WHERE r.name = 'Direktur' AND p.name = 'view_traffic_monitoring'
ON DUPLICATE KEY UPDATE role_id = VALUES(role_id);
```

### **Phase 7: Frontend Build**
```bash
# Build frontend (jika perlu)
cd frontend
npm run build

# Atau copy dist files ke web root
cp -r dist/* /var/www/html/
```

## ✅ Verification Checklist

### **Backend Verification:**
- [ ] Application starts without errors
- [ ] API endpoints accessible:
  - `GET /api/traffic/monitoring/dashboard`
  - `GET /api/traffic/monitoring/latest`
- [ ] Background jobs scheduled (check logs)
- [ ] Database table `traffic_history` created

### **Frontend Verification:**
- [ ] Menu "Traffic Monitoring" muncul di sidebar
- [ ] Halaman traffic monitoring bisa diakses
- [ ] Dashboard menampilkan data dengan benar
- [ ] Auto-refresh works
- [ ] Manual collection trigger works

### **Permissions Verification:**
- [ ] Admin role bisa akses traffic monitoring
- [ ] Direktur role bisa akses traffic monitoring
- [ ] Other roles sesuai kebutuhan

## 🚨 Troubleshooting

### **Common Issues:**

1. **Import Error:**
   ```bash
   # Check if all files uploaded correctly
   python -c "import app.models.traffic_history"
   python -c "import app.services.traffic_monitoring_service"
   python -c "import app.routers.traffic_monitoring"
   ```

2. **Database Migration Error:**
   ```bash
   # Check migration status
   alembic current

   # Force migration if stuck
   alembic stamp head
   ```

3. **Permission Denied:**
   ```bash
   # Check file permissions
   chmod 644 app/models/traffic_history.py
   chmod 644 app/services/traffic_monitoring_service.py
   ```

4. **Frontend Not Loading:**
   ```bash
   # Clear browser cache
   # Check browser console for errors
   # Verify API endpoints accessible
   ```

## 📞 Support

Jika ada masalah selama deployment:
1. Check error logs: `tail -f logs/app.log`
2. Verify database connection
3. Check all file permissions
4. Restart application service

---

**🎉 Traffic Monitoring System siap digunakan setelah semua checklist terpenuhi!**