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
          // 所有核心业务接口统一走 Node.js (NestJS) BFF
          '/api/auth': {
            changeOrigin: true,
            target: 'http://localhost:3000',
          },
          '/api/user': {
            changeOrigin: true,
            target: 'http://localhost:3000',
          },
          '/api/menu': {
            changeOrigin: true,
            target: 'http://localhost:3000',
          },
        },
      },
    },
  };
});
