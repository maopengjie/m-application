<script setup lang="ts">
interface Props {
  product?: any;
}

defineProps<Props>();
</script>

<template>
  <div class="product-card border rounded-lg p-4 shadow-sm hover:shadow-md transition-all dark:bg-zinc-900 dark:border-zinc-800 bg-white">
    <div class="product-image bg-gray-100 h-40 rounded-md mb-4 flex items-center justify-center dark:bg-zinc-800">
      <span class="text-gray-400 dark:text-zinc-500">商品图片</span>
    </div>
    <div class="product-info">
      <h3 class="text-lg font-semibold mb-2 dark:text-zinc-100">{{ product?.name || '商品名称' }}</h3>
      <p class="text-sm text-gray-500 mb-2 dark:text-zinc-400">型号: {{ product?.model || '-' }}</p>
      <div class="flex justify-between items-center">
        <span class="text-red-600 font-bold text-xl dark:text-red-500">¥{{ product?.price || '0.00' }}</span>
        <button class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors dark:bg-blue-700 dark:hover:bg-blue-600">查看详情</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 移除背景色的内联样式，改用 Tailwind 类处理，以便支持暗黑模式 */
</style>
