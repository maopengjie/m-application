<script setup lang="ts">
import type { PriceHistoryStats } from "#/api/types";

import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";

import { LineChart } from "echarts/charts";
import {
  DatasetComponent,
  GridComponent,
  MarkLineComponent,
  TooltipComponent,
  TransformComponent,
} from "echarts/components";
import { graphic } from "echarts/core";
import * as echarts from "echarts/core";
import { LabelLayout, LegacyGridContainLabel, UniversalTransition } from "echarts/features";
import { CanvasRenderer } from "echarts/renderers";
import { ElButton } from "element-plus";

import { getSkuPriceHistoryApi } from "#/api/product";

const props = defineProps<{
  skuId?: number | string;
}>();

echarts.use([
  TooltipComponent,
  GridComponent,
  DatasetComponent,
  TransformComponent,
  LineChart,
  CanvasRenderer,
  LabelLayout,
  LegacyGridContainLabel,
  UniversalTransition,
  MarkLineComponent,
]);

const chartRef = ref<HTMLElement | null>(null);
const activeRange = ref(30);
const loading = ref(false);
const error = ref<null | string>(null);
const stats = ref<PriceHistoryStats>({
  history: [],
  min_price: 0,
  max_price: 0,
  avg_price: 0,
  current_price: 0,
});

let chartInstance: echarts.ECharts | null = null;
let resizeTimer: null | ReturnType<typeof setTimeout> = null;

const debouncedResize = () => {
  if (resizeTimer) clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    resizeTimer = null;
    chartInstance?.resize();
  }, 100);
};

const insightText = computed(() => {
  if (loading.value || stats.value.history.length === 0) return "正在校准价格雷达...";

  const current = stats.value.current_price;
  const min = stats.value.min_price;
  const avg = stats.value.avg_price;
  const max = stats.value.max_price;

  const diffFromMin = current - min;
  const diffFromMinPercent = min > 0 ? (diffFromMin / min) * 100 : 0;

  let rangeText =
    activeRange.value === 7 ? "近一周" : (activeRange.value === 30 ? "近一月" : "近三月");

  if (current <= min) {
    return `🎉 太棒了！当前处于${rangeText}最低价，是绝对的买入黄金期。`;
  }

  if (diffFromMinPercent < 3) {
    return `🔥 该商品目前非常接近${rangeText}低点（仅高出 ¥${diffFromMin.toFixed(0)}），建议考虑入手。`;
  }

  if (current > avg) {
    const diffFromAvg = current - avg;
    return `⚠️ 当前处于价格高位，高于${rangeText}平均水平 ¥${diffFromAvg.toFixed(0)}。建议设置提醒，等待回落。`;
  }

  const progress = ((max - current) / (max - min)) * 100;
  return `📈 价格走势平稳。当前价已从峰值回落 ¥${(max - current).toFixed(0)}（回落进度 ${progress.toFixed(0)}%），处于温和区间。`;
});

const fetchHistory = async () => {
  if (!props.skuId) return;

  loading.value = true;
  error.value = null;
  try {
    const res = await getSkuPriceHistoryApi(props.skuId, activeRange.value);
    stats.value = res;
    // Wait for v-show to make the DOM visible and give it real dimensions
    await nextTick();
    initChart();
  } catch (error_: unknown) {
    const errMsg = error_ instanceof Error ? error_.message : "历史数据加载失败";
    error.value = errMsg;
  } finally {
    loading.value = false;
  }
};

const initChart = () => {
  if (!chartRef.value || stats.value.history.length === 0) return;
  if (chartRef.value.clientWidth === 0 || chartRef.value.clientHeight === 0) return;

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value);
  }

  const sortedHistory = stats.value.history.toSorted(
    (a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime(),
  );

  const option = {
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255, 255, 255, 0.98)",
      borderWidth: 0,
      shadowBlur: 15,
      shadowColor: "rgba(0,0,0,0.08)",
      textStyle: { color: "#18181b" },
      formatter: (params: any) => {
        const item = params[0];
        const date = new Date(item.name).toLocaleDateString();
        return `
          <div style="padding: 10px; font-family: sans-serif;">
            <div style="color: #a1a1aa; font-weight: 900; font-size: 10px; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.05em;">${date}</div>
            <div style="font-weight: 900; color: #ef4444; font-size: 18px; letter-spacing: -0.05em;">
              ¥${item.value}
            </div>
          </div>
        `;
      },
    },
    grid: { left: "2%", right: "5%", bottom: "10%", top: "15%", containLabel: true },

    xAxis: {
      type: "category",
      boundaryGap: false,
      data: sortedHistory.map((item) => item.recorded_at),
      axisLine: { show: false },
      axisLabel: {
        color: "#a1a1aa",
        fontSize: 10,
        fontWeight: 700,
        formatter: (value: string) => {
          const date = new Date(value);
          return `${date.getMonth() + 1}/${date.getDate()}`;
        },
      },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { type: "dashed", color: "rgba(244, 244, 245, 0.6)" } },
      axisLabel: { color: "#a1a1aa", fontSize: 10, fontWeight: 700 },
      scale: true,
    },
    series: [
      {
        type: "line",
        smooth: 0.4,
        data: sortedHistory.map((item) => item.price),
        symbol: "circle",
        symbolSize: 8,
        showSymbol: false,
        itemStyle: { color: "#3b82f6" },
        lineStyle: {
          width: 3,
          color: "#3b82f6",
          shadowBlur: 10,
          shadowColor: "rgba(59, 130, 246, 0.3)",
        },
        areaStyle: {
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(59, 130, 246, 0.15)" },
            { offset: 1, color: "rgba(59, 130, 246, 0)" },
          ]),
        },
        markLine: {
          silent: true,
          symbol: "none",
          label: { show: false },
          data: [{ type: "average", name: "均价" }],
          lineStyle: { type: "dashed", color: "rgba(161, 161, 170, 0.3)" },
        },
      },
    ],
  };

  chartInstance.setOption(option);
};

const handleResize = debouncedResize;

watch(
  () => props.skuId,
  () => fetchHistory(),
);
watch(activeRange, () => fetchHistory());

onMounted(() => {
  fetchHistory();
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  if (resizeTimer) clearTimeout(resizeTimer);
  window.removeEventListener("resize", handleResize);
  chartInstance?.dispose();
});
</script>

<template>
  <div class="space-y-6 w-full">
    <!-- Trend Ticker & Range -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="flex items-center gap-4">
        <div
          class="px-4 py-2 bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl border border-zinc-100 dark:border-zinc-800"
        >
          <div class="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">
            当前价
          </div>
          <div class="text-base font-black text-red-600 font-mono">¥{{ stats.current_price }}</div>
        </div>
        <div
          class="px-4 py-2 bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl border border-zinc-100 dark:border-zinc-800"
        >
          <div class="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">
            历史低点
          </div>
          <div class="text-base font-black text-green-600 font-mono">¥{{ stats.min_price }}</div>
        </div>
        <div
          class="px-4 py-2 bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl border border-zinc-100 dark:border-zinc-800 hidden sm:block"
        >
          <div class="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">
            均价参考
          </div>
          <div class="text-base font-black text-blue-600 font-mono">
            ¥{{ stats.avg_price.toFixed(0) }}
          </div>
        </div>
      </div>

      <div class="bg-zinc-100 dark:bg-zinc-800 p-1 rounded-xl flex self-end">
        <button
          v-for="range in [7, 30, 90]"
          :key="range"
          @click="activeRange = range"
          class="px-5 py-1.5 text-[10px] font-black rounded-lg transition-all"
          :class="[
            activeRange === range
              ? 'bg-white dark:bg-zinc-700 text-primary shadow-sm'
              : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300',
          ]"
        >
          {{ range }}D
        </button>
      </div>
    </div>

    <!-- Insight Banner -->
    <div
      class="bg-blue-50/50 dark:bg-blue-900/10 p-4 rounded-2xl border border-blue-100/50 dark:border-blue-900/20 flex items-center gap-3"
    >
      <span class="iconify lucide--sparkles text-blue-500 w-5 h-5 animate-pulse"></span>
      <p class="text-[11px] font-black text-blue-800 dark:text-blue-300 leading-tight">
        {{ insightText }}
      </p>
    </div>

    <!-- Chart Container -->
    <div class="relative min-h-[220px]">
      <div v-show="stats.history.length > 0" ref="chartRef" class="h-64 w-full"></div>

      <!-- Loading State -->
      <div
        v-if="loading"
        class="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-zinc-900/80 backdrop-blur-sm z-10 rounded-3xl"
      >
        <div class="flex flex-col items-center gap-3">
          <div
            class="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin"
          ></div>
          <span class="text-[10px] font-black text-zinc-400 uppercase tracking-widest">扫描历史价格...</span>
        </div>
      </div>

      <!-- Empty/Error State -->
      <div
        v-if="!loading && (error || stats.history.length === 0)"
        class="absolute inset-0 flex flex-col items-center justify-center bg-zinc-50/50 dark:bg-zinc-800/30 rounded-3xl border-2 border-dashed border-zinc-200 dark:border-zinc-700"
      >
        <span
          class="iconify lucide--line-chart text-zinc-300 dark:text-zinc-700 text-4xl mb-4"
        ></span>
        <p class="text-xs font-black text-zinc-400 uppercase tracking-widest mb-6">
          {{ error || "暂无该时段价格波动数据" }}
        </p>
        <ElButton
          v-if="error"
          size="default"
          type="primary"
          class="!rounded-xl"
          @click="fetchHistory"
        >
          重新同步数据
        </ElButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tracking-widest {
  letter-spacing: 0.1em;
}
</style>
