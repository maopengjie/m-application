<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';

const props = defineProps<{
  history?: any[];
}>();

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

const initChart = () => {
  if (!chartRef.value || !props.history) return;

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  // Sort history by date
  const sortedHistory = [...props.history].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>价格: <span style="font-weight: bold; color: #ef4444">¥{c}</span>'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '5%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: sortedHistory.map(item => new Date(item.date).toLocaleDateString()),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#9ca3af', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } },
      axisLabel: { color: '#9ca3af' }
    },
    series: [
      {
        name: 'Price',
        type: 'line',
        smooth: true,
        data: sortedHistory.map(item => item.price),
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#3b82f6' },
        lineStyle: { width: 3, color: '#3b82f6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0)' }
          ])
        }
      }
    ]
  };

  chartInstance.setOption(option);
};

const handleResize = () => {
  chartInstance?.resize();
};

watch(() => props.history, () => {
  initChart();
}, { deep: true });

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
});
</script>

<template>
  <div class="price-trend-chart">
    <div ref="chartRef" class="h-64 w-full"></div>
    <div v-if="!history || history.length === 0" class="absolute inset-0 flex items-center justify-center bg-gray-50/50 rounded-xl">
      <p class="text-gray-400 text-sm">暂无历史价格数据</p>
    </div>
  </div>
</template>

<style scoped>
.price-trend-chart {
  position: relative;
}
</style>
