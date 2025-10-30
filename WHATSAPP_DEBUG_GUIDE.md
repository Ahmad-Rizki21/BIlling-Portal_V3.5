# 🔍 WhatsApp Debugging Guide

## 🚨 **Problem:** Email masuk, WhatsApp tidak masuk

### **✅ Status Saat Ini:**
- ✅ Xendit API berhasil (200 OK)
- ✅ Email notification aktif
- ✅ `should_send_email: true` ✅
- ✅ `should_send_whatsapp: true` ✅
- ❌ WhatsApp tidak masuk ke +628986937819

---

## 🔧 **Solutions yang Diimplementasikan:**

### **1. Debug Logging** ✅
```python
# ✅ SUDAH DITAMBAHKAN di xendit_service.py
# Sekarang log akan menampilkan WhatsApp status detail:
# 📱 WhatsApp Notification Status:
#    should_send_whatsapp: true
#    notification_preference: {...}
#    customer_mobile: +628986937819
```

### **2. WhatsApp Opt-in Management** ✅
```bash
# ✅ API ENDPOINTS SEKARANG TERSEDIA:
# POST /whatsapp-optin/opt-in/{pelanggan_id}  - Request opt-in
# GET  /whatsapp-optin/status/{pelanggan_id}  - Check status
# POST /whatsapp-optin/test-message/{pelanggan_id} - Test message
```

### **3. Enhanced Xendit Payload** ✅
```python
# ✅ SUDAH DITAMBAHKAN:
payload = {
    # ... existing payload
    "should_send_email": True,      # ✅ Force enable
    "should_send_whatsapp": True,   # ✅ Force enable
}
```

---

## 📋 **IMMEDIATE ACTION PLAN:**

### **Step 1: Restart Application**
```bash
# Restart untuk apply debug logging
uvicorn app.main:app --reload
```

### **Step 2: Test New Invoice**
1. Buat invoice baru via UI
2. **Check log baru ini:**
```bash
# Log harus menampilkan:
📱 WhatsApp Notification Status:
   should_send_whatsapp: true
   notification_preference: {invoice_created: ["email", "whatsapp"], ...}
   customer_mobile: +628986937819
```

### **Step 3: Request Customer Opt-in**
```bash
# Request opt-in untuk ID pelanggan Anda:
curl -X POST "http://127.0.0.1:8000/whatsapp-optin/opt-in/4" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### **Step 4: Check WhatsApp Dashboard**
1. **Login** ke [Xendit Dashboard](https://dashboard.xendit.co)
2. **WhatsApp Business** → **Templates**
3. **Cari template:** `invoice_created`
4. **Status harus:** ✅ **Approved**
5. **WhatsApp Business** → **Overview**
6. **Status harus:** ✅ **Active**

---

## 🔍 **Most Likely Issues:**

### **🥇 WhatsApp Template Not Approved** (80% probability)
- **Check:** Xendit Dashboard → WhatsApp Business → Templates
- **Status:** "Pending" atau "Rejected" ❌
- **Solution:** Submit ulang template ke Xendit

### **🥈 Customer Opt-In Required** (70% probability)
- **Policy:** WhatsApp Business API requires explicit customer consent
- **Solution:** Request opt-in via API atau manual

### **🥉 WhatsApp Business Not Active** (50% probability)
- **Check:** Status WhatsApp Business di Xendit Dashboard
- **Solution:** Complete WhatsApp Business setup

### **🏆 Phone Number Issues** (30% probability)
- **Check:** Nomor +628986937819 aktif di WhatsApp
- **Solution:** Verify nomor dan format

---

## 📊 **Debugging Workflow:**

### **1. Check Log (Post-Restart)**
```bash
# Look for this pattern in logs:
📱 WhatsApp Notification Status:
should_send_whatsapp: true
notification_preference: {...}
```

### **2. Check Xendit Dashboard**
```bash
# 1. WhatsApp Business → Status: Active?
# 2. Templates → invoice_created: Approved?
# 3. Phone Numbers: Connected?
```

### **3. Test Opt-in**
```bash
# Request opt-in untuk customer:
POST /whatsapp-optin/opt-in/4
```

### **4. Manual Test**
```bash
# Kirim test message:
POST /whatsapp-optin/test-message/4?message=Test
```

---

## 🚀 **Alternative Solutions:**

### **Option A: Use SMS (Fallback)**
```python
# Tambahkan SMS fallback jika WhatsApp gagal
# Bisa integrasi dengan Twilio, Nexmo, atau provider lokal
```

### **Option B: In-App Notifications**
```python
# Tambahkan notifikasi di aplikasi web
# Browser notifications + dashboard alerts
```

### **Option C: Email-Only Mode**
```python
# Temporary disable WhatsApp jika masalah persist
payload = {
    "should_send_email": True,
    "should_send_whatsapp": False,  # Temporary disable
}
```

---

## 🎯 **Expected Results:**

### **✅ If WhatsApp Working:**
1. Email masuk ✅
2. WhatsApp masuk ✅
3. Log menampilkan detail status ✅

### **❌ If WhatsApp Still Not Working:**
1. Email masuk ✅
2. WhatsApp tidak masuk ❌
3. Log menampilkan Xendit error ❌
4. **Next:** Check Xendit Dashboard WhatsApp setup

---

## 📞 **Contact Xendit Support:**

If all debugging fails, contact Xendit support:

**Subject:** WhatsApp notifications not working
**Include:**
- Invoice ID: `690078026d09af96c3193cdb`
- Phone: `+628986937819`
- Email: `ahmad@ajnusa.com`
- Error logs
- WhatsApp Business status

---

## 📋 **Testing Checklist:**

- [ ] **Restart application** with new debug logging
- [ ] **Create new invoice** and check log
- [ ] **Check Xendit Dashboard** WhatsApp Business status
- [ ] **Verify template approval** (`invoice_created`)
- [ ] **Request customer opt-in** via API
- [ ] **Test manual WhatsApp** from Xendit
- [ ] **Check phone number** validity

---

## 🎉 **Next Steps:**

1. **Restart aplikasi** dulu
2. **Buat invoice baru** dan lihat log baru
3. **Share log WhatsApp status** di sini
4. **Saya akan bantu analyze** further!

**Let me know what the new logs show!** 🔍✨