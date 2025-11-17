# 🚀 Build Commands Guide - Artacom FTTH Billing

## ✅ **SEMUA COMMAND SUDAH TERSEDIAL!**

### **🏃‍♂️ Development Commands**
```bash
npm run dev              # Development server (host: true)
npm run dev:tsc          # Development + real-time TypeScript checking
```

### **🏗️ Build Production Commands**
```bash
npm run build           # Build dengan type checking
npm run build:prod      # Build production + analisis bundle
npm run build:fast      # Build cepat tanpa minify (untuk testing)
npm run build:preview   # Build + preview di browser
npm run build:report    # Build + analisis lengkap
npm run build-only      # Build tanpa type checking
```

### **📊 Analysis Commands**
```bash
npm run analyze:bundle  # Buka bundle analysis interactive
npm run analyze:size    # Tampilkan ukuran file
npm run performance     # Build + performance metrics
```

### **🧪 Quality Check Commands**
```bash
npm run type-check      # Check TypeScript errors
npm run type-check:watch # Watch TypeScript checking
npm run lint            # Fix linting issues
npm run lint:check      # Check linting tanpa fix
npm run format          # Format code dengan Prettier
npm run format:check    # Check formatting tanpa fix
```

### **🧪 Testing Commands**
```bash
npm run test            # Run unit tests
npm run test:unit       # Run tests once
npm run test:watch      # Watch mode testing
npm run test:coverage   # Test dengan coverage report
npm run test:e2e        # End-to-end testing
npm run test:e2e:dev    # E2E testing mode dev
```

### **🎯 Development Workflow Commands**
```bash
npm run pre-commit      # Semua checks sebelum commit
npm run clean           # Clean build cache
npm run clean:full      # Full reset + reinstall
```

### **🌐 Preview Commands**
```bash
npm run preview         # Preview build di port 4173
npm run serve           # Preview build (alias preview)
npm run serve:https     # Preview dengan HTTPS
```

---

## 📋 **Recommended Workflow**

### **🔧 Daily Development**
```bash
# 1. Start development
npm run dev

# 2. Periodic checks (sebelum commit)
npm run pre-commit
```

### **🧪 Before Pull Request**
```bash
# 1. Quality checks
npm run type-check
npm run lint:check
npm run format:check

# 2. Build test
npm run build:fast

# 3. Preview build
npm run build:preview
```

### **🚀 Production Deployment**
```bash
# 1. Production build dengan analisis
npm run build:prod

# 2. Check bundle analysis
npm run analyze:bundle

# 3. Check performance
npm run analyze:size

# 4. Deploy (sesuai deployment method)
# (copy dist/ folder ke server)
```

---

## 📊 **Build Results Analysis**

### **✅ Latest Build Results:**
- **Total Bundle Size:** 9.3 MB (uncompressed)
- **Build Time:** ~56 seconds
- **Number of Chunks:** 9 optimized chunks
- **TypeScript:** ✅ No errors
- **Bundle Analysis:** ✅ Interactive treemap generated

### **📈 Bundle Breakdown (Gzipped):**
| File | Size | Gzipped | Type |
|------|------|---------|------|
| **vue-vendor.js** | 1.24 MB | 326 kB | Vue + Router + Pinia |
| **file-utils.js** | 618 kB | 185 kB | XLSX + Canvas utils |
| **charts-svg.js** | 267 kB | 90 kB | ECharts library |
| **vendor.js** | 180 kB | 61 kB | Other vendors |
| **maps.js** | 149 kB | 43 kB | Leaflet maps |
| **CSS Files** | 1.40 MB | 200 kB | All stylesheets |

### **🎯 Performance Optimization Status:**
- ✅ **Code Splitting:** Smart chunking enabled
- ✅ **Minification:** Terser enabled
- ✅ **Tree Shaking:** Dead code eliminated
- ✅ **Asset Optimization:** Images & fonts optimized
- ⚠️ **Large Chunks:** Fonts & Vue vendor > 1MB (normal untuk large apps)

---

## 🚀 **Quick Reference**

```bash
# Development
npm run dev              # Start coding

# Production Build
npm run build:prod       # Build for production

# Analysis
npm run analyze:bundle   # Visual bundle analysis
npm run analyze:size     # Check file sizes

# Quality Checks
npm run pre-commit       # All checks before commit
npm run build:preview    # Test production build
```

---

## 💡 **Pro Tips**

1. **Fast Development:** Use `npm run dev:tsc` untuk real-time TypeScript checking
2. **Quick Testing:** Use `npm run build:fast` untuk build cepat tanpa minify
3. **Bundle Analysis:** `npm run analyze:bundle` buka interactive visualization
4. **Before Commit:** Always run `npm run pre-commit`
5. **Production Ready:** `npm run build:prod` gives you production-ready build with analysis

---

**🎉 Semua command ready to use! Build kamu sudah enterprise-grade!**