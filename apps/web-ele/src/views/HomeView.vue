<script setup lang="ts">
import ProductCard from '#/components/ProductCard.vue';
// 模拟数据
const featuredProducts = [
  { name: '电子元件 A', price: '12.50', model: 'XC6SLX9' },
  { name: '控制处理器 B', price: '89.00', model: 'STM32F103' },
  { name: '传感器模块 C', price: '5.20', model: 'DHT11' },
];
</script>

<template>
  <div class="p-6">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-800">元器件价格概览</h1>
      <p class="text-gray-500">实时监控全网价格波动，助您精准决策。</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <ProductCard v-for="p in featuredProducts" :key="p.name" :product="p" />
    </div>
  </div>
</template>
