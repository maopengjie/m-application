<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';
import type {
  CoreDashboardOverview,
  DashboardAlertItem,
  PriceTimeSeriesListItem,
  ScrapeTaskOverview,
  ScrapeTaskRun,
  SkuComparison,
} from '#/api';
import type { AnomalyAlert } from '#/api/data-cleaning';

import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';
import { ElButton, ElEmpty, ElSkeleton, ElTag } from 'element-plus';

import {
  getCoreDashboardOverviewApi,
  getPriceTimeSeriesListApi,
  getScrapeTaskOverviewApi,
  getScrapeTaskRunsApi,
  getSkuComparisonsApi,
} from '#/api';
import { getAnomaliesApi } from '#/api/data-cleaning';

const loading = ref(true);
const overview = ref<CoreDashboardOverview | null>(null);
const scrapeOverview = ref<null | ScrapeTaskOverview>(null);
const pendingAnomalies = ref<AnomalyAlert[]>([]);
const recentProblemRuns = ref<ScrapeTaskRun[]>([]);
const lowestPriceItems = ref<PriceTimeSeriesListItem[]>([]);
const pendingComparisons = ref<SkuComparison[]>([]);
const priceOpportunitySummary = ref({
  lowestPriceSkuCount: 0,
  totalSnapshotCount: 0,
});
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

const problemRunCount = computed(() => {
  const statusCounts = scrapeOverview.value?.statusCounts ?? {};
  return (
    (statusCounts.FAILED ?? 0) +
    (statusCounts.PARTIAL_SUCCESS ?? 0) +
    (statusCounts.TIMEOUT ?? 0)
  );
});

const workbenchItems = computed(() => {
  const data = overview.value;
  const scrape = scrapeOverview.value;

  return [
    {
      action: '处理异常',
      count: data?.pendingAnomalyCount ?? 0,
      description: '价格异常、数据缺失和抓取失败需要人工确认',
      tone: 'danger',
      title: '待核验异常',
      to: {
        path: '/data-center/data-cleaning',
        query: { status: 'pending', tab: 'anomalies' },
      },
      unit: '条',
    },
    {
      action: '查看失败项',
      count: problemRunCount.value,
      description: scrape?.latestProblemRun?.summaryMessage || '失败、超时、部分成功任务会进入这里',
      tone: problemRunCount.value > 0 ? 'danger' : 'success',
      title: '问题抓取任务',
      to: {
        path: '/data-center/sku-repository',
        query: scrape?.latestProblemRun
          ? { runId: String(scrape.latestProblemRun.id), taskStatus: 'problem' }
          : { taskStatus: 'problem' },
      },
      unit: '个',
    },
    {
      action: '查看价格',
      count: data?.alertItems.length ?? 0,
      description: '过去 1 小时价格跌幅最大的 SKU',
      tone: (data?.alertItems.length ?? 0) > 0 ? 'warning' : 'success',
      title: '价格异动',
      to: {
        path: '/data-center/price-time-series',
        query: {
          recent: '1h',
          sku: data?.alertItems[0]?.sku_id,
        },
      },
      unit: '个',
    },
    {
      action: '确认同款',
      count: pendingComparisons.value.length,
      description: 'AI 候选同款关系等待人工确认或驳回',
      tone: pendingComparisons.value.length > 0 ? 'warning' : 'success',
      title: '待确认同款',
      to: {
        path: '/data-center/mapping-center',
        query: { tab: 'comparison', status: 'pending' },
      },
      unit: '组',
    },
    {
      action: '跟踪队列',
      count: scrape?.openRunCount ?? 0,
      description: `排队 ${getStatusCount('PENDING')} / 执行 ${getStatusCount('RUNNING')}`,
      tone: (scrape?.openRunCount ?? 0) > 0 ? 'primary' : 'neutral',
      title: '开放抓取任务',
      to: {
        path: '/data-center/sku-repository',
        query: { taskStatus: 'open' },
      },
      unit: '个',
    },
  ];
});

const todayCollectionStatus = computed(() => {
  const scrape = scrapeOverview.value;
  const latest = scrape?.latestRun;
  const successRate = scrape?.successRate ?? overview.value?.successRate ?? 0;
  const openRunCount = scrape?.openRunCount ?? 0;
  const failedCount = problemRunCount.value;
  const status =
    failedCount > 0 ? '有失败待处理' : openRunCount > 0 ? '采集中' : '运行平稳';

  return {
    failedCount,
    latest,
    openRunCount,
    status,
    successRate,
  };
});

const highPriorityActions = computed(() => {
  const actions = [
    {
      count: pendingAnomalies.value.length,
      label: '处理异常',
      tone: 'danger',
      to: anomalyRoute(),
    },
    {
      count: recentProblemRuns.value.length,
      label: '重试失败任务',
      tone: 'warning',
      to: { path: '/data-center/sku-repository', query: { taskStatus: 'problem' } },
    },
    {
      count: pendingComparisons.value.length,
      label: '确认同款',
      tone: 'primary',
      to: { path: '/data-center/mapping-center', query: { tab: 'comparison' } },
    },
  ];

  return actions.filter((item) => item.count > 0);
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

function getStatusCount(status: string) {
  return scrapeOverview.value?.statusCounts[status] ?? 0;
}

function workbenchCardClass(tone: string) {
  return {
    danger: 'border-rose-200 bg-rose-50/70 dark:border-rose-500/30 dark:bg-rose-500/10',
    neutral: 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900',
    primary: 'border-blue-200 bg-blue-50/70 dark:border-blue-500/30 dark:bg-blue-500/10',
    success: 'border-emerald-200 bg-emerald-50/70 dark:border-emerald-500/30 dark:bg-emerald-500/10',
    warning: 'border-amber-200 bg-amber-50/70 dark:border-amber-500/30 dark:bg-amber-500/10',
  }[tone];
}

function workbenchTagType(tone: string) {
  if (tone === 'danger') return 'danger';
  if (tone === 'success') return 'success';
  if (tone === 'warning') return 'warning';
  if (tone === 'primary') return 'primary';
  return 'info';
}

function topAlertItems() {
  return (overview.value?.alertItems ?? []).slice(0, 5);
}

function topLowestPriceItems() {
  return lowestPriceItems.value.slice(0, 5);
}

function topPendingComparisons() {
  return pendingComparisons.value.slice(0, 5);
}

function collectionStatusType() {
  if (todayCollectionStatus.value.failedCount > 0) return 'danger';
  if (todayCollectionStatus.value.openRunCount > 0) return 'primary';
  return 'success';
}

function actionButtonType(tone: string) {
  if (tone === 'danger') return 'danger';
  if (tone === 'warning') return 'warning';
  if (tone === 'primary') return 'primary';
  if (tone === 'success') return 'success';
  return 'info';
}

function formatTaskName(taskName: string) {
  if (taskName === 'scrape_product') return '单商品抓取';
  if (taskName === 'scrape_active_products') return '批量抓取';
  if (taskName === 'sync_jd_category_tree') return '类目同步';
  return taskName;
}

function formatRunStatusLabel(status: string) {
  if (status === 'SUCCESS') return '成功';
  if (status === 'PARTIAL_SUCCESS') return '部分成功';
  if (status === 'FAILED') return '失败';
  if (status === 'TIMEOUT') return '超时';
  if (status === 'RUNNING') return '执行中';
  return '排队中';
}

function problemRunRoute(run: ScrapeTaskRun) {
  return {
    path: '/data-center/sku-repository',
    query: { runId: String(run.id), taskStatus: 'problem' },
  };
}

function anomalyRoute() {
  return {
    path: '/data-center/data-cleaning',
    query: { status: 'pending', tab: 'anomalies' },
  };
}

function priceAlertRoute(item: DashboardAlertItem) {
  return {
    path: '/data-center/price-time-series',
    query: { recent: '1h', sku: item.sku_id },
  };
}

function lowestPriceRoute(item: PriceTimeSeriesListItem) {
  return {
    path: '/data-center/price-time-series',
    query: { sku: item.skuId },
  };
}

function comparisonRoute() {
  return {
    path: '/data-center/mapping-center',
    query: { tab: 'comparison' },
  };
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
    const [
      overviewData,
      scrapeData,
      anomalies,
      failedRuns,
      partialRuns,
      timeoutRuns,
      priceData,
      comparisonData,
    ] =
    await Promise.all([
      getCoreDashboardOverviewApi(),
      getScrapeTaskOverviewApi(),
      getAnomaliesApi({ is_verified: 0, limit: 5 }),
      getScrapeTaskRunsApi({ limit: 5, status: 'FAILED' }),
      getScrapeTaskRunsApi({ limit: 5, status: 'PARTIAL_SUCCESS' }),
      getScrapeTaskRunsApi({ limit: 5, status: 'TIMEOUT' }),
      getPriceTimeSeriesListApi({ page: 1, pageSize: 20 }),
      getSkuComparisonsApi({ page: 1, pageSize: 100 }),
    ]);
    overview.value = overviewData;
    scrapeOverview.value = scrapeData;
    pendingAnomalies.value = anomalies;
    recentProblemRuns.value = [...failedRuns, ...partialRuns, ...timeoutRuns]
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
      .slice(0, 5);
    lowestPriceItems.value = priceData.items
      .filter((item) => item.lowestPrice > 0 && item.currentPrice === item.lowestPrice)
      .sort((a, b) => b.latestCaptureAt.localeCompare(a.latestCaptureAt))
      .slice(0, 5);
    pendingComparisons.value = comparisonData.items
      .filter((item) => item.status === 0)
      .slice(0, 5);
    priceOpportunitySummary.value = {
      lowestPriceSkuCount: priceData.summary.lowestPriceSkuCount,
      totalSnapshotCount: priceData.summary.totalSnapshotCount,
    };
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
    <div class="mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div class="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
        <div class="min-w-0">
          <div class="flex flex-wrap items-center gap-3">
            <h1 class="text-xl font-bold text-slate-950 dark:text-slate-100">数据中心运营工作台</h1>
            <ElTag effect="light" :type="collectionStatusType()">
              今日采集：{{ todayCollectionStatus.status }}
            </ElTag>
          </div>
          <div class="mt-3 grid gap-3 text-sm text-slate-500 md:grid-cols-4">
            <div>
              <span class="text-slate-400">成功率</span>
              <strong class="ml-2 text-slate-800 dark:text-slate-100">
                {{ todayCollectionStatus.successRate.toFixed(1) }}%
              </strong>
            </div>
            <div>
              <span class="text-slate-400">开放任务</span>
              <strong class="ml-2 text-slate-800 dark:text-slate-100">
                {{ formatNumber(todayCollectionStatus.openRunCount) }}
              </strong>
            </div>
            <div>
              <span class="text-slate-400">失败/超时</span>
              <strong class="ml-2 text-slate-800 dark:text-slate-100">
                {{ formatNumber(todayCollectionStatus.failedCount) }}
              </strong>
            </div>
            <div>
              <span class="text-slate-400">最新任务</span>
              <strong class="ml-2 text-slate-800 dark:text-slate-100">
                {{ todayCollectionStatus.latest ? formatRunStatusLabel(todayCollectionStatus.latest.status) : '暂无' }}
              </strong>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap gap-3">
          <RouterLink
            v-for="action in highPriorityActions"
            :key="action.label"
            :to="action.to"
          >
            <ElButton :type="actionButtonType(action.tone)" plain>
              {{ action.label }} {{ action.count }}
            </ElButton>
          </RouterLink>
          <RouterLink
            v-if="highPriorityActions.length === 0"
            :to="{ path: '/data-center/price-time-series', query: { recent: '24h' } }"
          >
            <ElButton type="success" plain>查看价格机会</ElButton>
          </RouterLink>
        </div>
      </div>
    </div>

    <div class="metric-grid mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div
        v-for="item in metricCards"
        :key="item.label"
        class="metric-card overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
      >
        <div class="metric-card__glow bg-gradient-to-br" :class="item.accent" />
        <div class="relative z-10">
          <div class="text-sm text-slate-500 dark:text-slate-400">{{ item.subLabel }}</div>
          <div class="mt-2 text-base font-medium text-slate-700 dark:text-slate-300">{{ item.label }}</div>
          <div class="mt-4 text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            {{ item.value }}
          </div>
        </div>
      </div>
    </div>

    <div class="workbench-grid mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-5">
      <div
        v-for="item in workbenchItems"
        :key="item.title"
        class="workbench-card rounded-2xl border p-4 shadow-sm"
        :class="workbenchCardClass(item.tone)"
      >
        <div class="mb-4 flex items-start justify-between gap-3">
          <div>
            <div class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ item.title }}</div>
            <div class="mt-2 flex items-end gap-2">
              <span class="text-3xl font-bold tracking-tight text-slate-950 dark:text-slate-100">
                {{ formatNumber(item.count) }}
              </span>
              <span class="pb-1 text-sm text-slate-500">{{ item.unit }}</span>
            </div>
          </div>
          <ElTag effect="light" :type="workbenchTagType(item.tone)">
            {{ item.count > 0 ? '待处理' : '正常' }}
          </ElTag>
        </div>
        <p class="min-h-10 text-sm leading-5 text-slate-500">
          {{ item.description }}
        </p>
        <RouterLink :to="item.to">
          <ElButton class="mt-4 w-full" plain type="primary">
            {{ item.action }}
          </ElButton>
        </RouterLink>
      </div>
    </div>

    <div class="mb-5 grid gap-4 lg:grid-cols-3">
      <div class="role-card border-emerald-200 bg-emerald-50 dark:border-emerald-500/30 dark:bg-emerald-500/10">
        <div class="text-sm font-semibold text-emerald-700 dark:text-emerald-300">运营工作台</div>
        <div class="mt-3 text-2xl font-bold text-slate-950 dark:text-slate-100">{{ topAlertItems().length }}</div>
        <p class="mt-2 text-sm text-slate-600 dark:text-slate-400">关注价格异动、历史低价和促销变化。</p>
        <RouterLink :to="{ path: '/data-center/price-time-series', query: { recent: '1h' } }">
          <ElButton class="mt-4" plain type="success">查看价格机会</ElButton>
        </RouterLink>
      </div>
      <div class="role-card border-amber-200 bg-amber-50 dark:border-amber-500/30 dark:bg-amber-500/10">
        <div class="text-sm font-semibold text-amber-700 dark:text-amber-300">数据治理工作台</div>
        <div class="mt-3 text-2xl font-bold text-slate-950 dark:text-slate-100">{{ pendingAnomalies.length }}</div>
        <p class="mt-2 text-sm text-slate-600 dark:text-slate-400">处理异常、清洗结果和同款映射确认。</p>
        <RouterLink :to="anomalyRoute()">
          <ElButton class="mt-4" plain type="warning">进入治理队列</ElButton>
        </RouterLink>
      </div>
      <div class="role-card border-blue-200 bg-blue-50 dark:border-blue-500/30 dark:bg-blue-500/10">
        <div class="text-sm font-semibold text-blue-700 dark:text-blue-300">技术运维工作台</div>
        <div class="mt-3 text-2xl font-bold text-slate-950 dark:text-slate-100">{{ problemRunCount }}</div>
        <p class="mt-2 text-sm text-slate-600 dark:text-slate-400">关注抓取成功率、失败任务和调度状态。</p>
        <RouterLink :to="{ path: '/data-center/sku-repository', query: { taskStatus: 'problem' } }">
          <ElButton class="mt-4" plain type="primary">查看任务健康</ElButton>
        </RouterLink>
      </div>
    </div>

    <div class="mb-5 grid gap-5 xl:grid-cols-3 2xl:grid-cols-5">
      <div class="card-box p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">最近失败任务 Top 5</h2>
            <p class="mt-1 text-sm text-slate-500">按更新时间聚合失败、超时和部分成功任务。</p>
          </div>
          <RouterLink :to="{ path: '/data-center/sku-repository', query: { taskStatus: 'problem' } }">
            <ElButton link type="primary">全部</ElButton>
          </RouterLink>
        </div>
        <div v-if="recentProblemRuns.length" class="space-y-3">
          <RouterLink
            v-for="run in recentProblemRuns"
            :key="run.id"
            class="todo-row"
            :to="problemRunRoute(run)"
          >
            <div class="min-w-0">
              <div class="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                #{{ run.id }} {{ run.summaryMessage || formatTaskName(run.taskName) }}
              </div>
              <div class="mt-1 text-xs text-slate-500">
                {{ run.updatedAt }} · 成功 {{ run.successCount }} / 失败 {{ run.failureCount }}
              </div>
            </div>
            <ElTag type="danger">{{ formatRunStatusLabel(run.status) }}</ElTag>
          </RouterLink>
        </div>
        <ElEmpty v-else description="暂无失败任务" :image-size="72" />
      </div>

      <div class="card-box p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">待核验异常 Top 5</h2>
            <p class="mt-1 text-sm text-slate-500">最新进入异常队列的待处理记录。</p>
          </div>
          <RouterLink :to="anomalyRoute()">
            <ElButton link type="primary">处理</ElButton>
          </RouterLink>
        </div>
        <div v-if="pendingAnomalies.length" class="space-y-3">
          <RouterLink
            v-for="item in pendingAnomalies"
            :key="item.id"
            class="todo-row"
            :to="anomalyRoute()"
          >
            <div class="min-w-0">
              <div class="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                {{ item.skuId }} · {{ item.message || item.alertValue }}
              </div>
              <div class="mt-1 text-xs text-slate-500">
                {{ item.platform }} · {{ item.createdAt }}
              </div>
            </div>
            <ElTag type="warning">{{ item.alertType }}</ElTag>
          </RouterLink>
        </div>
        <ElEmpty v-else description="暂无待核验异常" :image-size="72" />
      </div>

      <div class="card-box p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">价格跌幅 Top 5</h2>
            <p class="mt-1 text-sm text-slate-500">过去 1 小时价格下探最明显的 SKU。</p>
          </div>
          <RouterLink :to="{ path: '/data-center/price-time-series', query: { recent: '1h' } }">
            <ElButton link type="primary">查看</ElButton>
          </RouterLink>
        </div>
        <div v-if="topAlertItems().length" class="space-y-3">
          <RouterLink
            v-for="item in topAlertItems()"
            :key="item.sku_id"
            class="todo-row"
            :to="priceAlertRoute(item)"
          >
            <div class="min-w-0">
              <div class="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                {{ item.product_name }}
              </div>
              <div class="mt-1 text-xs text-slate-500">
                SKU {{ item.sku_id }} · {{ formatCurrency(item.previous_price) }} → {{ formatCurrency(item.current_price) }}
              </div>
            </div>
            <span class="alert-tag" :class="alertTagClass(item)">
              -{{ item.drop_percent.toFixed(1) }}%
            </span>
          </RouterLink>
        </div>
        <ElEmpty v-else description="过去 1 小时暂无价格异动" :image-size="72" />
      </div>

      <div class="card-box p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">历史低价商品</h2>
            <p class="mt-1 text-sm text-slate-500">
              当前命中历史低价的商品，全部 {{ formatNumber(priceOpportunitySummary.lowestPriceSkuCount) }} 个。
            </p>
          </div>
          <RouterLink :to="{ path: '/data-center/price-time-series', query: { recent: '24h' } }">
            <ElButton link type="primary">查看</ElButton>
          </RouterLink>
        </div>
        <div v-if="topLowestPriceItems().length" class="space-y-3">
          <RouterLink
            v-for="item in topLowestPriceItems()"
            :key="item.id"
            class="todo-row"
            :to="lowestPriceRoute(item)"
          >
            <div class="min-w-0">
              <div class="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                {{ item.productName }}
              </div>
              <div class="mt-1 text-xs text-slate-500">
                SKU {{ item.skuId }} · 当前 {{ formatCurrency(item.currentPrice) }}
              </div>
            </div>
            <ElTag type="success">历史低价</ElTag>
          </RouterLink>
        </div>
        <ElEmpty v-else description="暂无历史低价商品" :image-size="72" />
      </div>

      <div class="card-box p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">待确认同款</h2>
            <p class="mt-1 text-sm text-slate-500">AI 自动匹配后的候选关系，需要人工确认。</p>
          </div>
          <RouterLink :to="comparisonRoute()">
            <ElButton link type="primary">处理</ElButton>
          </RouterLink>
        </div>
        <div v-if="topPendingComparisons().length" class="space-y-3">
          <RouterLink
            v-for="item in topPendingComparisons()"
            :key="item.id"
            class="todo-row"
            :to="comparisonRoute()"
          >
            <div class="min-w-0">
              <div class="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                {{ item.masterSku?.productName || `基准商品 #${item.masterSkuId}` }}
              </div>
              <div class="mt-1 truncate text-xs text-slate-500">
                {{ item.linkedSku?.platform || '竞品' }} · {{ item.linkedSku?.productName || `候选 #${item.linkedSkuId}` }}
              </div>
            </div>
            <ElTag type="warning">{{ item.matchScore ?? 0 }}%</ElTag>
          </RouterLink>
        </div>
        <ElEmpty v-else description="暂无待确认同款" :image-size="72" />
      </div>
    </div>

    <div class="grid gap-5 2xl:grid-cols-[minmax(0,1.6fr)_420px]">
      <div class="card-box p-5">
        <div class="mb-4 flex items-start justify-between gap-3">
          <div>
            <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">实时抓取流</h2>
            <p class="mt-1 text-sm text-slate-500">
              监控当前正在抓取的 SKU 规模和过去 1 小时成功率波动。
            </p>
          </div>
          <div v-if="overview" class="rounded-xl bg-slate-50 px-4 py-3 text-right dark:bg-slate-800/70">
            <div class="text-xs text-slate-500 dark:text-slate-400">最新刷新</div>
            <div class="mt-1 text-sm font-medium text-slate-800 dark:text-slate-200">
              {{ overview.captureTimeline.at(-1)?.timestamp }}
            </div>
          </div>
        </div>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="h-[320px] rounded-2xl bg-slate-100 dark:bg-slate-800" />
          </template>
          <EchartsUI ref="captureChartRef" class="h-[320px]" />
        </el-skeleton>
      </div>

      <div class="alert-wall card-box p-5">
        <div class="mb-4">
          <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">价格异动预警墙</h2>
          <p class="mt-1 text-sm text-slate-500">滚动显示过去 1 小时内价格跌幅最大的商品。</p>
        </div>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="space-y-3">
              <div v-for="index in 5" :key="index" class="h-16 rounded-xl bg-slate-100 dark:bg-slate-800" />
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
                  <div class="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
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
          <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">数据总量统计</h2>
          <p class="mt-1 text-sm text-slate-500">展示当前库内商品总数、价格记录规模与平台覆盖情况。</p>
        </div>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="h-32 rounded-2xl bg-slate-100 dark:bg-slate-800" />
              <div class="h-32 rounded-2xl bg-slate-100 dark:bg-slate-800" />
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
              class="rounded-2xl border border-slate-200 px-4 py-3 dark:border-slate-800 dark:bg-slate-900/70"
            >
              <div class="mb-2 flex items-center justify-between text-sm">
                <span class="font-medium text-slate-700 dark:text-slate-300">{{ item.platform }}</span>
                <span class="text-slate-500">
                  {{ formatNumber(item.sku_count) }} / {{ item.percent.toFixed(1) }}%
                </span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div class="platform-progress h-full rounded-full" :style="{ width: `${item.percent}%` }" />
              </div>
            </div>
          </div>
        </el-skeleton>
      </div>

      <div class="card-box p-5">
        <div class="mb-4">
          <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100">平台分布</h2>
          <p class="mt-1 text-sm text-slate-500">按平台查看库内 SKU 覆盖占比。</p>
        </div>

        <el-skeleton :loading="loading" animated>
          <template #template>
            <div class="h-[320px] rounded-2xl bg-slate-100 dark:bg-slate-800" />
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

.dark .alert-row {
  border-color: rgb(30 41 59);
  background: linear-gradient(180deg, rgb(15 23 42), rgb(2 6 23));
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

.todo-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid rgb(226 232 240);
  border-radius: 14px;
  background: rgb(248 250 252);
  padding: 12px;
  transition: all 0.2s ease;
}

.dark .todo-row {
  border-color: rgb(30 41 59);
  background: rgb(15 23 42);
}

.todo-row:hover {
  border-color: rgb(147 197 253);
  background: rgb(239 246 255);
}

.dark .todo-row:hover {
  border-color: rgb(59 130 246 / 0.55);
  background: rgb(30 41 59);
}

.role-card {
  border-width: 1px;
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 8px 24px rgb(15 23 42 / 0.05);
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
