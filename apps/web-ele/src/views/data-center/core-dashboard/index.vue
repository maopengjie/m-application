<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';
import type {
  CoreDashboardOverview,
  DashboardAlertItem,
} from '#/api';

import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';
import { ElEmpty, ElSkeleton } from 'element-plus';

import { getCoreDashboardOverviewApi } from '#/api';

const loading = ref(true);
const overview = ref<CoreDashboardOverview | null>(null);
const captureChartRef = ref<EchartsUIType>();
const platformChartRef = ref<EchartsUIType>();
const captureChart = useEcharts(captureChartRef);
const platformChart = useEcharts(platformChartRef);

let refreshTimer: ReturnType<typeof setInterval> | null = null;

const metricCards = computed(() => {
  const data = overview.value;
  if (!data) {
    return [];
  }

  const peakCapture = Math.max(...data.captureTimeline.map((item) => item.active_sku_count));
  const avgSuccessRate = Math.round(
    (data.captureTimeline.reduce((sum, item) => sum + item.success_rate, 0) /
      data.captureTimeline.length) *
      10,
  ) / 10;

  return [
    {
      accent: 'from-sky-500/20 to-cyan-500/5',
      label: '当前抓取 SKU',
      subLabel: '实时抓取流',
      value: formatNumber(data.activeSkuCount),
    },
    {
      accent: 'from-emerald-500/20 to-teal-500/5',
      label: '抓取成功率',
      subLabel: '近 1 小时均值',
      value: `${data.successRate.toFixed(1)}%`,
    },
    {
      accent: 'from-amber-500/20 to-orange-500/5',
      label: '近 1 小时峰值',
      subLabel: '活跃抓取波峰',
      value: formatNumber(peakCapture),
    },
    {
      accent: 'from-violet-500/20 to-fuchsia-500/5',
      label: '平均成功率',
      subLabel: '趋势稳定性',
      value: `${avgSuccessRate.toFixed(1)}%`,
    },
  ];
});

const alertMarqueeItems = computed(() => {
  const items = overview.value?.alertItems ?? [];
  return items.length > 0 ? [...items, ...items] : [];
});

const platformBreakdown = computed(() => {
  const total = overview.value?.totalSkuCount ?? 0;
  return (overview.value?.platformBreakdown ?? []).map((item) => ({
    ...item,
    percent: total > 0 ? Math.round((item.sku_count / total) * 1000) / 10 : 0,
  }));
});

function formatNumber(value: number) {
  return new Intl.NumberFormat('zh-CN').format(value);
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('zh-CN', {
    currency: 'CNY',
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    style: 'currency',
  }).format(value);
}

function renderCharts(data: CoreDashboardOverview) {
  void nextTick(async () => {
    await captureChart.renderEcharts({
      color: ['#2563eb', '#10b981'],
      grid: {
        bottom: 24,
        containLabel: true,
        left: 8,
        right: 8,
        top: 28,
      },
      legend: {
        right: 0,
        textStyle: {
          color: '#64748b',
        },
      },
      series: [
        {
          areaStyle: {
            opacity: 0.12,
          },
          data: data.captureTimeline.map((item) => item.active_sku_count),
          name: '抓取 SKU',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          type: 'line',
        },
        {
          data: data.captureTimeline.map((item) => item.success_rate),
          name: '成功率',
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          type: 'line',
          yAxisIndex: 1,
        },
      ],
      tooltip: {
        trigger: 'axis',
      },
      xAxis: {
        axisLabel: {
          color: '#94a3b8',
        },
        axisLine: {
          lineStyle: {
            color: '#e2e8f0',
          },
        },
        axisTick: {
          show: false,
        },
        boundaryGap: false,
        data: data.captureTimeline.map((item) => item.timestamp),
        type: 'category',
      },
      yAxis: [
        {
          axisLabel: {
            color: '#94a3b8',
          },
          splitLine: {
            lineStyle: {
              color: '#e2e8f0',
            },
          },
          type: 'value',
        },
        {
          axisLabel: {
            color: '#94a3b8',
            formatter: '{value}%',
          },
          max: 100,
          min: 90,
          splitLine: {
            show: false,
          },
          type: 'value',
        },
      ],
    });

    await platformChart.renderEcharts({
      color: ['#0f766e', '#2563eb', '#f59e0b'],
      legend: {
        bottom: 0,
        icon: 'circle',
        textStyle: {
          color: '#64748b',
        },
      },
      series: [
        {
          center: ['50%', '42%'],
          data: data.platformBreakdown.map((item) => ({
            name: item.platform,
            value: item.sku_count,
          })),
          label: {
            formatter: '{b}\n{d}%',
          },
          radius: ['45%', '68%'],
          type: 'pie',
        },
      ],
      tooltip: {
        formatter: (params: any) =>
          `${params.name}<br/>SKU 数量：${formatNumber(Number(params.value ?? 0))}`,
      },
    });
  });
}

async function loadOverview() {
  loading.value = true;
  try {
    overview.value = await getCoreDashboardOverviewApi();
  } finally {
    loading.value = false;
  }
}

watch(
  overview,
  (data) => {
    if (data) {
      renderCharts(data);
    }
  },
  { deep: true },
);

onMounted(async () => {
  await loadOverview();
  refreshTimer = setInterval(() => {
    void loadOverview();
  }, 30_000);
});

onBeforeUnmount(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
});

function alertTagClass(item: DashboardAlertItem) {
  if (item.drop_percent >= 20) return 'is-critical';
  if (item.drop_percent >= 12) return 'is-warning';
  return 'is-normal';
}
</script>

<template>
  <div class="core-dashboard-page p-5">
    <div class="metric-grid mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div
        v-for="item in metricCards"
        :key="item.label"
        class="metric-card overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <div class="metric-card__glow bg-gradient-to-br" :class="item.accent" />
        <div class="relative z-10">
          <div class="text-sm text-slate-500">{{ item.subLabel }}</div>
          <div class="mt-2 text-base font-medium text-slate-700">{{ item.label }}</div>
          <div class="mt-4 text-3xl font-semibold tracking-tight text-slate-900">
            {{ item.value }}
          </div>
        </div>
      </div>
    </div>

    <div class="grid gap-5 2xl:grid-cols-[minmax(0,1.6fr)_420px]">
      <div class="card-box p-5">
        <div class="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900">实时抓取流</h2>
            <p class="mt-1 text-sm text-slate-500">
              监控当前正在抓取的 SKU 规模和过去 1 小时成功率波动。
            </p>
          </div>
          <div v-if="overview" class="rounded-xl bg-slate-50 px-4 py-3 text-right">
            <div class="text-xs text-slate-500">最新刷新</div>
            <div class="mt-1 text-sm font-medium text-slate-800">
              {{ overview.captureTimeline.at(-1)?.timestamp }}
            </div>
          </div>
        </div>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="h-[320px] rounded-2xl bg-slate-100" />
          </template>
          <EchartsUI ref="captureChartRef" class="h-[320px]" />
        </el-skeleton>
      </div>

      <div class="alert-wall card-box p-5">
        <div class="mb-4">
          <h2 class="text-lg font-bold text-slate-900">价格异动预警墙</h2>
          <p class="mt-1 text-sm text-slate-500">滚动显示过去 1 小时内价格跌幅最大的商品。</p>
        </div>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="space-y-3">
              <div v-for="index in 5" :key="index" class="h-16 rounded-xl bg-slate-100" />
            </div>
          </template>

          <el-empty
            v-if="!(overview?.alertItems.length)"
            description="过去 1 小时暂无价格异动"
          />

          <div v-else class="alert-wall__viewport">
            <div class="alert-wall__track" :class="{ 'is-animated': overview.alertItems.length > 4 }">
              <article
                v-for="(item, index) in alertMarqueeItems"
                :key="`${item.sku_id}-${index}`"
                class="alert-row"
              >
                <div class="min-w-0 flex-1">
                  <div class="truncate text-sm font-medium text-slate-900">
                    {{ item.product_name }}
                  </div>
                  <div class="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span>{{ item.platform }}</span>
                    <span>SKU {{ item.sku_id }}</span>
                    <span>{{ item.detected_at }}</span>
                  </div>
                </div>
                <div class="ml-3 text-right">
                  <div class="text-xs text-slate-400 line-through">
                    {{ formatCurrency(item.previous_price) }}
                  </div>
                  <div class="text-sm font-semibold text-rose-600">
                    {{ formatCurrency(item.current_price) }}
                  </div>
                  <div class="mt-1">
                    <span class="alert-tag" :class="alertTagClass(item)">
                      -{{ item.drop_percent.toFixed(1) }}%
                    </span>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </el-skeleton>
      </div>
    </div>

    <div class="mt-5 grid gap-5 2xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
      <div class="card-box p-5">
        <div class="mb-4">
          <h2 class="text-lg font-bold text-slate-900">数据总量统计</h2>
          <p class="mt-1 text-sm text-slate-500">展示当前库内商品总数、价格记录规模与平台覆盖情况。</p>
        </div>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="h-32 rounded-2xl bg-slate-100" />
              <div class="h-32 rounded-2xl bg-slate-100" />
            </div>
          </template>

          <div v-if="overview" class="grid gap-4 lg:grid-cols-[repeat(2,minmax(0,1fr))]">
            <div class="stats-card rounded-2xl bg-slate-950 p-5 text-white">
              <div class="text-sm text-slate-300">商品总数</div>
              <div class="mt-4 text-4xl font-semibold tracking-tight">
                {{ formatNumber(overview.totalSkuCount) }}
              </div>
              <div class="mt-3 text-sm text-slate-400">覆盖多平台标准化商品资产库</div>
            </div>

            <div class="stats-card rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 p-5 text-white">
              <div class="text-sm text-emerald-50">价格记录总条数</div>
              <div class="mt-4 text-4xl font-semibold tracking-tight">
                {{ formatNumber(overview.totalPriceRecords) }}
              </div>
              <div class="mt-3 text-sm text-emerald-100">可支撑价格趋势与异动分析</div>
            </div>
          </div>

          <div v-if="platformBreakdown.length" class="mt-5 space-y-4">
            <div
              v-for="item in platformBreakdown"
              :key="item.platform"
              class="rounded-2xl border border-slate-200 px-4 py-3"
            >
              <div class="mb-2 flex items-center justify-between text-sm">
                <span class="font-medium text-slate-700">{{ item.platform }}</span>
                <span class="text-slate-500">
                  {{ formatNumber(item.sku_count) }} / {{ item.percent.toFixed(1) }}%
                </span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-slate-100">
                <div class="platform-progress h-full rounded-full" :style="{ width: `${item.percent}%` }" />
              </div>
            </div>
          </div>
        </el-skeleton>
      </div>

      <div class="card-box p-5">
        <div class="mb-4">
          <h2 class="text-lg font-bold text-slate-900">平台分布</h2>
          <p class="mt-1 text-sm text-slate-500">按平台查看库内 SKU 覆盖占比。</p>
        </div>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="h-[320px] rounded-2xl bg-slate-100" />
          </template>
          <EchartsUI ref="platformChartRef" class="h-[320px]" />
        </el-skeleton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  position: relative;
}

.metric-card__glow {
  position: absolute;
  inset: 0;
}

.alert-wall__viewport {
  height: 420px;
  mask-image: linear-gradient(
    to bottom,
    transparent 0,
    black 24px,
    black calc(100% - 24px),
    transparent 100%
  );
  overflow: hidden;
}

.alert-wall__track {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-block: 6px;
}

.alert-wall__track.is-animated {
  animation: alert-scroll 18s linear infinite;
}

.alert-wall__viewport:hover .alert-wall__track.is-animated {
  animation-play-state: paused;
}

.alert-row {
  display: flex;
  align-items: center;
  border: 1px solid rgb(226 232 240);
  border-radius: 16px;
  background: linear-gradient(180deg, rgb(255 255 255), rgb(248 250 252));
  padding: 14px;
}

.alert-tag {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
}

.alert-tag.is-critical {
  background: rgb(254 226 226);
  color: rgb(190 24 93);
}

.alert-tag.is-warning {
  background: rgb(255 237 213);
  color: rgb(194 65 12);
}

.alert-tag.is-normal {
  background: rgb(254 249 195);
  color: rgb(161 98 7);
}

.platform-progress {
  background: linear-gradient(90deg, rgb(14 165 233), rgb(37 99 235));
}

@keyframes alert-scroll {
  0% {
    transform: translateY(0);
  }

  100% {
    transform: translateY(calc(-50% - 6px));
  }
}
</style>
