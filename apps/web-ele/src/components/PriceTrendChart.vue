<script setup lang="ts">
import { onMounted, ref } from 'vue';
// 这里未来可以引入 ECharts 或其他图表库

const chartRef = ref<HTMLElement | null>(null);

onMounted(() => {
  if (chartRef.value) {
    // 初始化图表逻辑
  }
});
</script>

<template>
  <div class="price-trend-chart">
    <div ref="chartRef" class="h-64 w-full bg-gray-50 flex items-center justify-center border border-dashed rounded">
      <p class="text-gray-400">价格趋势图表区域</p>
    </div>
  </div>
</template>
