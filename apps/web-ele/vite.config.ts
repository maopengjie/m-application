import { defineConfig } from '@vben/vite-config';

import ElementPlus from 'unplugin-element-plus/vite';

export default defineConfig(async () => {
  const backendTarget = 'http://localhost:8000';

  return {
    application: {},
    vite: {
      plugins: [
        ElementPlus({
          format: 'esm',
        }),
      ],
      server: {
        proxy: {
          '/api/sku-repository': {
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, ''),
            target: backendTarget,
            ws: true,
          },
          '/api/data-cleaning': {
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, ''),
            target: backendTarget,
            ws: true,
          },
          '/api/core-dashboard': {
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, ''),
            target: backendTarget,
            ws: true,
          },
          '/api': {
            changeOrigin: true,
            rewrite: (path) => path.replace(/^\/api/, ''),
            // mock代理目标地址
            target: 'http://localhost:5320/api',
            ws: true,
          },
        },
      },
    },
  };
});
