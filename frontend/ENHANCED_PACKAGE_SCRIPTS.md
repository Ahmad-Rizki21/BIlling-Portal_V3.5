# 📦 Enhanced Package.json Scripts

## Tambahkan scripts ini di package.json:

```json
{
  "scripts": {
    "dev": "vite --host",
    "dev:tsc": "run-p dev \"type-check {@}\" --",

    "build": "run-p type-check \"build-only {@}\" --",
    "build:prod": "npm run build && npm run build:analyze",
    "build:analyze": "npm run build && open dist/bundle-analysis.html",
    "build:preview": "npm run build && npm run preview",
    "build:report": "npm run build && npm run build:performance",
    "build:fast": "vite build --minify=false",

    "build-only": "vite build",
    "preview": "vite preview --port 4173 --host",

    "type-check": "vue-tsc --build --force",
    "type-check:watch": "vue-tsc --build --watch",

    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix --ignore-path .gitignore",
    "lint:check": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --ignore-path .gitignore",
    "lint:staged": "lint-staged",

    "format": "prettier --write src/",
    "format:check": "prettier --check src/",
    "format:staged": "prettier --write --staged",

    "test": "vitest",
    "test:unit": "vitest run",
    "test:watch": "vitest watch",
    "test:coverage": "vitest --coverage",
    "test:e2e": "cypress run",
    "test:e2e:dev": "cypress open",

    "analyze:bundle": "npx vite-bundle-analyzer dist",
    "analyze:size": "bundlesize",
    "build:performance": "npm run build && npm run lighthouse:ci",

    "lighthouse": "npx lighthouse http://localhost:3000 --output=html --output-path=./lighthouse-report.html --quiet",
    "lighthouse:ci": "npm run build && npx lighthouse http://localhost:4173 --output=html --output-path=./lighthouse-report.html --chrome-flags='--headless'",

    "clean": "rm -rf dist node_modules/.vite",
    "clean:full": "rm -rf dist node_modules package-lock.json && npm install",

    "pre-commit": "npm run type-check && npm run lint:check && npm run format:check",

    "deploy:staging": "npm run build:prod && deploy-staging",
    "deploy:production": "npm run build:prod && deploy-production"
  }
}
```

## 🎯 Command Berdasarkan Use Case:

### **🔧 Daily Development**
```bash
npm run dev          # Development server
npm run dev:tsc      # Development + type checking
npm run lint         # Fix code issues
npm run format       # Format code
```

### **🧪 Quality Assurance**
```bash
npm run type-check   # Check TypeScript
npm run lint:check   # Check linting (no fix)
npm run format:check # Check formatting
npm run test         # Run tests
npm run pre-commit   # All checks before commit
```

### **🚀 Build Production**
```bash
# Fast build (untuk testing cepat)
npm run build:fast

# Standard production build
npm run build

# Production build dengan analisis
npm run build:prod

# Build + performance check
npm run build:performance
```

### **📊 Analysis & Monitoring**
```bash
npm run analyze:bundle    # Deep bundle analysis
npm run analyze:size      # Track bundle size
npm run lighthouse        # Performance audit
npm run build:report      # Full build report
```

### **🧹 Maintenance**
```bash
npm run clean         # Clean build cache
npm run clean:full    # Full reset
```

## 📋 Recommended Workflow:

### **1. Development Cycle**
```bash
# Start development
npm run dev:tsc

# During development (periodically)
npm run lint
npm run format
```

### **2. Before Commit**
```bash
npm run pre-commit
```

### **3. Pre-Deployment**
```bash
npm run build:prod
npm run analyze:bundle
npm run lighthouse
```

### **4. Production Deploy**
```bash
npm run deploy:production
```

## ⚡ Performance Commands:

```bash
# Quick performance check
npm run lighthouse

# CI/CD performance check
npm run lighthouse:ci

# Bundle size monitoring
npm run analyze:size
```

## 🎛️ Environment-Specific:

```bash
# Development
npm run dev

# Staging
npm run build:prod
npm run deploy:staging

# Production
npm run build:prod
npm run deploy:production
```