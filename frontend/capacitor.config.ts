// capacitor.config.ts (VERSI PERBAIKAN)

import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.billingftth.my.id', 
  appName: 'Portal FTTH',
  webDir: 'dist',
  server: {
    url: 'https://billingftth.my.id', // URL Cloudflare Anda
    cleartext: true
  }
};

export default config;