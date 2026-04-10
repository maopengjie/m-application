import { defineConfig } from '@vben/vite-config';

import ElementPlus from 'unplugin-element-plus/vite';

export default defineConfig(async () => {
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
          // 系统、权限、管理相关接口 -> Node.js (NestJS)
          '/api/auth': {
            changeOrigin: true,
            target: 'http://localhost:3000',
          },
          '/api/user': {
            changeOrigin: true,
            target: 'http://localhost:3000',
          },
          // 爬虫、数据分析相关接口 -> Python (FastAPI)
          '/api/crawler': {
            changeOrigin: true,
            target: 'http://localhost:8000',
          },
          '/api/analysis': {
            changeOrigin: true,
            target: 'http://localhost:8000',
          },
        },
      },
    },
  };
});
