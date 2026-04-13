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
          // 所有接口统一指向 Python (FastAPI) 数据引擎
          '/api': {
            changeOrigin: true,
            target: 'http://localhost:8000',
          },
        },
      },
    },
  };
});
