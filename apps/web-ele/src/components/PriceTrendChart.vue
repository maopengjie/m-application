<script setup lang="ts">
import { onMounted, ref, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import { getSkuPriceHistoryApi } from '#/api/product';
import type { PriceHistoryStats } from '#/api/types';

const props = defineProps<{
  skuId?: number | string;
}>();

const chartRef = ref<HTMLElement | null>(null);
const activeRange = ref(30);
const loading = ref(false);
const error = ref<string | null>(null);
const stats = ref<PriceHistoryStats>({
  history: [],
  min_price: 0,
  max_price: 0,
  avg_price: 0,
  current_price: 0
});

let chartInstance: echarts.ECharts | null = null;

const fetchHistory = async () => {
  if (!props.skuId) return;
  
  loading.value = true;
  error.value = null;
  try {
    const res = await getSkuPriceHistoryApi(props.skuId, activeRange.value);
    stats.value = res;
    initChart();
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : '历史数据加载失败，请重试';
    console.error('Failed to fetch price history:', err);
    error.value = errMsg;
  } finally {
    loading.value = false;
  }
};

const initChart = () => {
  if (!chartRef.value || !stats.value.history) return;

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  const sortedHistory = [...stats.value.history].sort((a, b) => 
    new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime()
  );

  interface TooltipParam {
    name: string;
    value: number;
    data: any;
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderWidth: 0,
      shadowBlur: 10,
      shadowColor: 'rgba(0,0,0,0.1)',
      formatter: (params: TooltipParam[]) => {
        const item = params[0];
        const date = new Date(item.name).toLocaleDateString();
        return `
          <div style="padding: 8px;">
            <div style="color: #9ca3af; font-size: 12px; margin-bottom: 4px;">${date}</div>
            <div style="font-weight: bold; color: #1f2937; font-size: 16px;">
              ¥${item.value}
            </div>
          </div>
        `;
      }
    },
    grid: {
      left: '2%',
      right: '2%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: sortedHistory.map(item => item.recorded_at),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { 
        color: '#9ca3af', 
        fontSize: 10,
        formatter: (value: string) => {
          const date = new Date(value);
          return `${date.getMonth() + 1}/${date.getDate()}`;
        }
      },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } },
      axisLabel: { color: '#9ca3af', fontSize: 10 },
      scale: true // Auto adjust y-axis range
    },
    series: [
      {
        name: '价格',
        type: 'line',
        smooth: true,
        data: sortedHistory.map(item => item.price),
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        itemStyle: { color: '#3b82f6' },
        lineStyle: { width: 3, color: '#3b82f6' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0)' }
          ])
        },
        markLine: {
            silent: true,
            symbol: 'none',
            label: { show: false },
            data: [{ type: 'average', name: '平均价' }],
            lineStyle: { type: 'dashed', color: 'rgba(59, 130, 246, 0.3)' }
        }
      }
    ]
  };

  chartInstance.setOption(option);
};

const handleResize = () => {
  chartInstance?.resize();
};

watch(() => props.skuId, () => {
  fetchHistory();
});

watch(activeRange, () => {
  fetchHistory();
});

onMounted(() => {
  fetchHistory();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
});
</script>

<template>
  <div class="price-trend-chart-container">
    <!-- Range Selector -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex gap-4">
        <div class="stat-item">
          <div class="text-xs text-gray-400 mb-1">当前价</div>
          <div class="text-lg font-bold text-red-500">¥{{ stats.current_price }}</div>
        </div>
        <div class="stat-item">
          <div class="text-xs text-gray-400 mb-1">历史最低</div>
          <div class="text-lg font-bold text-green-500">¥{{ stats.min_price }}</div>
        </div>
        <div class="stat-item">
          <div class="text-xs text-gray-400 mb-1">平均价</div>
          <div class="text-lg font-bold text-blue-500">¥{{ stats.avg_price.toFixed(2) }}</div>
        </div>
      </div>
      
      <div class="bg-gray-100 dark:bg-zinc-800 p-1 rounded-lg flex">
        <button 
          v-for="range in [7, 30, 90]" 
          :key="range"
          @click="activeRange = range"
          :class="[
            'px-4 py-1 text-xs font-medium rounded-md transition-all',
            activeRange === range 
              ? 'bg-white dark:bg-zinc-700 text-blue-600 dark:text-blue-400 shadow-sm' 
              : 'text-gray-500 dark:text-zinc-400 hover:text-gray-700 dark:hover:text-zinc-200'
          ]"
        >
          {{ range }}天
        </button>
      </div>
    </div>

    <!-- Chart -->
    <div class="relative">
      <div ref="chartRef" class="h-64 w-full"></div>
      
      <!-- Loading Overlay -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-white/50 dark:bg-zinc-900/50 backdrop-blur-[1px] z-10 rounded-xl">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>

      <!-- Error State -->
      <div v-if="!loading && error" class="absolute inset-0 flex flex-col items-center justify-center bg-red-50/50 dark:bg-red-900/10 rounded-xl border border-red-100 dark:border-red-900/20">
        <span class="iconify lucide--alert-circle text-red-500 text-4xl mb-2"></span>
        <p class="text-red-500 text-sm mb-3">{{ error }}</p>
        <el-button size="small" type="primary" plain @click="fetchHistory">点击重试</el-button>
      </div>

      <!-- No Data -->
      <div v-if="!loading && !error && (!stats.history || stats.history.length === 0)" class="absolute inset-0 flex flex-col items-center justify-center bg-gray-50/50 dark:bg-zinc-800/50 rounded-xl">
        <span class="iconify lucide--bar-chart-2 text-gray-300 text-4xl mb-2"></span>
        <p class="text-gray-400 text-sm">暂无该时段价格数据</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.price-trend-chart-container {
  width: 100%;
}
.stat-item {
  @apply px-4 border-r border-gray-100 dark:border-zinc-800 last:border-0;
}
</style>
