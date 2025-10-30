# 🚀 Rate Limiter Integration Guide

## ⚡ Quick Integration (1 Minute Setup)

### Step 1: Add Import
```python
# Di file yang memanggil create_xendit_invoice, tambahkan:
from app.services.rate_limiter import create_invoice_with_rate_limit, InvoicePriority
```

### Step 2: Replace Function Call
```python
# ❌ ORIGINAL:
result = await create_xendit_invoice(invoice, pelanggan, paket, deskripsi, pajak, no_telp)

# ✅ WITH RATE LIMITING:
result = await create_invoice_with_rate_limit(
    invoice, pelanggan, paket, deskripsi, pajak, no_telp,
    priority=InvoicePriority.NORMAL  # Optional: HIGH, NORMAL, LOW
)
```

### Step 3: Done! 🎉

---

## 📦 Bulk Operations (For Monthly Billing)

```python
from app.services.rate_limiter import create_bulk_invoices_with_rate_limit

# Prepare data
invoices_data = []
for invoice_data in monthly_invoices:
    invoices_data.append({
        'invoice': invoice_data['invoice'],
        'pelanggan': invoice_data['pelanggan'],
        'paket': invoice_data['paket'],
        'deskripsi_xendit': invoice_data['deskripsi'],
        'pajak': invoice_data['pajak'],
        'no_telp_xendit': invoice_data.get('no_telp', ''),
        'priority': InvoicePriority.NORMAL
    })

# Process dengan rate limiting
result = await create_bulk_invoices_with_rate_limit(invoices_data)
```

---

## 📊 Monitoring

```python
from app.services.rate_limiter import rate_limiter

# Check queue status
status = await rate_limiter.get_queue_status()
print(f"Queue: {status['pending']} pending, {status['processing']} processing")

# Retry failed invoices
await rate_limiter.retry_failed_invoices()
```

---

## 🎯 Priority Levels

- **HIGH**: VIP customers, urgent invoices
- **NORMAL**: Regular customers (default)
- **LOW**: Bulk operations, non-urgent

---

## ✅ Benefits

1. **No Rate Limiting Errors** - Automatic rate limiting (2 req/s)
2. **All Invoices Delivered** - Automatic retry with exponential backoff
3. **Queue System** - Handle bulk operations smoothly
4. **Zero Logic Changes** - Your business logic stays the same
5. **Monitoring** - Track progress and handle failures

---

## 🚨 Error Handling

Rate limiter automatically handles:
- **Rate limiting** - Adds delay when needed
- **Network errors** - Retries with exponential backoff
- **API timeouts** - Retries up to 3 times
- **Queue failures** - Failed invoices can be retried manually

---

## 📝 What Changed?

✅ **ADDED:**
- Rate limiting (2 requests/second for Xendit)
- Automatic retry (3 attempts with exponential backoff)
- Queue system for bulk operations
- Error recovery and monitoring
- Priority handling

❌ **NOT CHANGED:**
- Your business logic
- Xendit API calls
- Invoice creation flow
- Database operations
- Error handling logic

---

## 🔧 Advanced Usage

```python
# Custom priority based on customer type
priority = InvoicePriority.HIGH if customer.is_vip else InvoicePriority.NORMAL

# Monitor queue progress
while True:
    status = await rate_limiter.get_queue_status()
    if status['pending'] == 0 and status['processing'] == 0:
        break
    await asyncio.sleep(5)

# Handle specific failures
if status['failed'] > 0:
    await rate_limiter.retry_failed_invoices()
```

---

## 🎉 Integration Complete!

Your system now has:
- ✅ Rate limiting protection
- ✅ Automatic retry logic
- ✅ Queue processing
- ✅ Error recovery
- ✅ Monitoring capabilities

**All invoices will be delivered to users (WhatsApp + Email) without rate limiting errors!** 🚀