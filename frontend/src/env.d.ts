/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Electron API interface
interface Window {
  electronAPI?: {
    platform: string;
    version: string;
    getVersions: () => NodeJS.ProcessVersions;
  };
}