<script lang="ts" setup>
import type { FormInstance } from 'element-plus';

import type { EchartsUIType } from '@vben/plugins/echarts';

import type {
  PriceTimeSeriesDetail,
  PriceTimeSeriesListItem,
  PriceTimeSeriesSummary,
} from '#/api';

import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';

import { EchartsUI, useEcharts } from '@vben/plugins/echarts';

import {
  ElButton,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElOption,
  ElPagination,
  ElSelect,
  ElSkeleton,
  ElTable,
  ElTableColumn,
  ElTag,
  ElMessage,
} from 'element-plus';

import {
  getPriceTimeSeriesDetailApi,
  getPriceTimeSeriesListApi,
} from '#/api';

interface QueryFormState {
  keyword: string;
  page: number;
  pageSize: number;
  platform: string;
  status: -1 | 0 | 1 | '';
}

const queryFormRef = ref<FormInstance>();
const timelineChartRef = ref<EchartsUIType>();
const timelineChart = useEcharts(timelineChartRef);
const route = useRoute();

const loading = ref(false);
const detailLoading = ref(false);
const tableData = ref<PriceTimeSeriesListItem[]>([]);
const total = ref(0);
const summary = ref<null | PriceTimeSeriesSummary>(null);
const selectedProductId = ref<number>();
const detail = ref<null | PriceTimeSeriesDetail>(null);

const queryForm = reactive<QueryFormState>({
  keyword: '',
  page: 1,
  pageSize: 8,
  platform: '',
  status: 1,
});

const platformOptions = [
  { label: '京东', value: 'jd' },
  { label: '天猫', value: 'tmall' },
  { label: '拼多多', value: 'pdd' },
];

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '在售', value: 1 },
  { label: '下架', value: 0 },
  { label: '删除', value: -1 },
];

const metricCards = computed(() => {
  const currentSummary = summary.value;
  const currentDetail = detail.value;
  if (!currentSummary) {
    return [];
  }

  return [
    {
      accent: 'from-cyan-500/25 to-sky-500/5',
      label: 'SKU 轨迹数',
      value: formatNumber(currentSummary.totalSkuCount),
    },
    {
      accent: 'from-emerald-500/25 to-teal-500/5',
      label: '抓取快照',
      value: formatNumber(currentSummary.totalSnapshotCount),
    },
    {
      accent: 'from-amber-500/25 to-orange-500/5',
      label: '促销模型记录',
      value: formatNumber(currentSummary.activePromotionCount),
    },
    {
      accent: 'from-rose-500/25 to-pink-500/5',
      label: '历史低价命中率',
      value: `${currentSummary.lowestPriceSkuCount}/${currentSummary.totalSkuCount}`,
    },
    {
      accent: 'from-violet-500/25 to-fuchsia-500/5',
      label: '平均折扣率',
      value: `${currentSummary.avgDiscountRate.toFixed(1)}%`,
    },
    {
      accent: 'from-slate-500/20 to-slate-400/5',
      label: '当前选中价差',
      value: currentDetail
        ? formatCurrency(currentDetail.priceExtremes.priceSpan)
        : '--',
    },
  ];
});

const selectedProduct = computed(() =>
  tableData.value.find((item) => item.id === selectedProductId.value) ?? null,
);

type InsightTone = 'danger' | 'info' | 'primary' | 'success' | 'warning';

const priceInsightCards = computed(() => {
  const currentDetail = detail.value;
  if (!currentDetail || currentDetail.timeline.length === 0) {
    return [];
  }
  const product = currentDetail.product;
  const extremes = currentDetail.priceExtremes;
  const isHistoricalLow = extremes.currentPrice > 0 && extremes.currentPrice === extremes.lowestPrice;
  return [
    {
      label: '历史低价提醒',
      tone: (isHistoricalLow ? 'danger' : 'success') as InsightTone,
      value: isHistoricalLow ? '当前命中历史低价' : `距低价差 ${formatCurrency(extremes.currentPrice - extremes.lowestPrice)}`,
    },
    {
      label: '价格波动区间',
      tone: 'info' as const,
      value: `${formatCurrency(extremes.lowestPrice)} - ${formatCurrency(extremes.highestPrice)}`,
    },
    {
      label: '促销拆解',
      tone: (currentDetail.promotionRecords.length > 0 ? 'warning' : 'info') as InsightTone,
      value: currentDetail.promotionRecords.length > 0
        ? `共 ${currentDetail.promotionRecords.length} 条促销公式`
        : '暂无促销公式',
    },
    {
      label: '同款比价',
      tone: 'primary' as const,
      value: product.brandName ? `${product.brandName} 同款待接入` : '同款对比待接入',
    },
    {
      label: '异常排除',
      tone: (currentDetail.timeline.some((item) => item.isAnomalous) ? 'danger' : 'success') as InsightTone,
      value: currentDetail.timeline.some((item) => item.isAnomalous)
        ? '存在异常点已标记'
        : '当前轨迹无异常点',
    },
  ];
});

const routeFilterHint = computed(() => {
  if (route.query.recent === '1h' && route.query.sku) {
    return `已按最近 1 小时价格异动 SKU「${route.query.sku}」筛选`;
  }
  if (route.query.recent === '1h') {
    return '已从今日监控进入，可优先查看最近 1 小时价格异动 SKU';
  }
  return '';
});

function hasPriceHistory(item: Pick<PriceTimeSeriesListItem, 'captureCount'> | null | undefined) {
  return Boolean(item && item.captureCount > 0);
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('zh-CN', {
    currency: 'CNY',
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    style: 'currency',
  }).format(value);
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('zh-CN').format(value);
}

function normalizeQuery() {
  return {
    keyword: queryForm.keyword || undefined,
    page: queryForm.page,
    pageSize: queryForm.pageSize,
    platform: queryForm.platform || undefined,
    status: queryForm.status === '' ? undefined : queryForm.status,
  };
}

function applyRouteQuery() {
  if (typeof route.query.sku === 'string' && route.query.sku) {
    queryForm.keyword = route.query.sku;
    queryForm.page = 1;
  }
}

async function loadList() {
  loading.value = true;
  try {
    const data = await getPriceTimeSeriesListApi(normalizeQuery());
    tableData.value = data.items;
    total.value = data.total;
    summary.value = data.summary;

    const nextId =
      data.items.find((item) => item.id === selectedProductId.value)?.id ?? data.items[0]?.id;
    selectedProductId.value = nextId;
    if (nextId) {
      await loadDetail(nextId);
    } else {
      detail.value = null;
    }
  } catch (error) {
    console.error('Failed to load price list:', error);
    ElMessage.error('加载价格时序数据失败');
  } finally {
    loading.value = false;
  }
}

async function loadDetail(productId: number) {
  selectedProductId.value = productId;
  detailLoading.value = true;
  try {
    detail.value = await getPriceTimeSeriesDetailApi(productId);
  } catch (error: any) {
    console.error('Failed to load price detail:', error);
    detail.value = null;
    // Only show error if it's not a 404 (timeline not found)
    if (error?.response?.status !== 404) {
      ElMessage.error('加载详情图表失败');
    }
  } finally {
    detailLoading.value = false;
  }
}

function handleSearch() {
  queryForm.page = 1;
  void loadList();
}

function handleReset() {
  queryFormRef.value?.resetFields();
  queryForm.keyword = '';
  queryForm.page = 1;
  queryForm.pageSize = 8;
  queryForm.platform = '';
  queryForm.status = 1;
  void loadList();
}

function handlePageChange(page: number) {
  queryForm.page = page;
  void loadList();
}

function handlePageSizeChange(pageSize: number) {
  queryForm.page = 1;
  queryForm.pageSize = pageSize;
  void loadList();
}

function handleRowClick(row: PriceTimeSeriesListItem) {
  void loadDetail(row.id);
}

function renderTimelineChart(data: PriceTimeSeriesDetail) {
  if (data.timeline.length === 0) {
    void nextTick(async () => {
      await timelineChart.renderEcharts({
        graphic: {
          left: 'center',
          style: {
            fill: '#94a3b8',
            font: '14px sans-serif',
            text: '暂无历史价格轨迹',
          },
          top: 'middle',
          type: 'text',
        },
        xAxis: {
          show: false,
          type: 'category',
        },
        yAxis: {
          show: false,
          type: 'value',
        },
        series: [],
      });
    });
    return;
  }

  const maxFinalPrice = Math.max(...data.timeline.map((item) => item.finalPrice));
  void nextTick(async () => {
    await timelineChart.renderEcharts({
      color: ['#0f766e', '#2563eb'],
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
          data: data.timeline.map((item) => item.listPrice),
          name: '标价',
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          type: 'line',
        },
        {
          areaStyle: {
            opacity: 0.18,
          },
          data: data.timeline.map((item) => item.finalPrice),
          markLine: {
            data: [
              {
                label: {
                  formatter: '均价: {c}',
                  position: 'insideEndBottom',
                },
                lineStyle: {
                  color: '#64748b',
                  type: 'dashed',
                },
                name: '平均价',
                yAxis: data.priceExtremes.averagePrice,
              },
            ],
            symbol: ['none', 'none'],
          },
          markPoint: {
            data: [
              ...data.timeline
                .filter((item) => item.isHistoricalLow)
                .map((item) => ({
                  coord: [item.capturedAt, item.finalPrice],
                  name: '历史低价',
                  value: item.finalPrice,
                })),
              ...data.timeline
                .filter((item) => item.finalPrice === maxFinalPrice)
                .map((item) => ({
                  coord: [item.capturedAt, item.finalPrice],
                  itemStyle: {
                    color: '#f59e0b',
                  },
                  label: {
                    formatter: '高点',
                  },
                  name: '历史最高',
                  value: item.finalPrice,
                })),
            ],
            symbolSize: 40,
          },
          name: '到手价',
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          type: 'line',
        },
      ],
      tooltip: {
        formatter: (params: any) => {
          const date = params[0].axisValue;
          let html = `<div class="font-bold mb-1">${date}</div>`;
          params.forEach((item: any) => {
            html += `<div class="flex items-center justify-between gap-4">
              <span class="flex items-center gap-1">
                <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:${item.color};"></span>
                ${item.seriesName}
              </span>
              <span class="font-bold">¥${item.value.toFixed(2)}</span>
            </div>`;
          });

          // Find the snapshot for this date to show promo text
          const snapshot = data.timeline.find((s) => s.capturedAt === date);
          if (snapshot?.promoText) {
            html += `<div class="mt-2 pt-2 border-t border-slate-200 text-xs text-slate-500 italic">
              ${snapshot.promoText}
            </div>`;
          }
          return html;
        },
        trigger: 'axis',
      },
      xAxis: {
        axisLabel: {
          color: '#94a3b8',
          formatter: (value: string) => value.slice(5, 16),
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
        data: data.timeline.map((item) => item.capturedAt),
        type: 'category',
      },
      yAxis: {
        axisLabel: {
          color: '#94a3b8',
          formatter: (value: number) => `¥${value}`,
        },
        splitLine: {
          lineStyle: {
            color: '#e2e8f0',
          },
        },
        type: 'value',
      },
    });
  });
}

watch(
  detail,
  (data) => {
    if (data) {
      renderTimelineChart(data);
    }
  },
  { deep: true },
);

onMounted(async () => {
  applyRouteQuery();
  await loadList();
});

watch(
  () => route.query.sku,
  async () => {
    applyRouteQuery();
    await loadList();
  },
);
</script>

<template>
  <div class="price-time-series-page p-5">
    <div class="metric-grid mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      <div
        v-for="item in metricCards"
        :key="item.label"
        class="metric-card overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900"
      >
        <div class="metric-card__glow bg-gradient-to-br" :class="item.accent"></div>
        <div class="relative z-10">
          <div class="text-sm text-slate-500 dark:text-slate-400">{{ item.label }}</div>
          <div class="mt-4 text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            {{ item.value }}
          </div>
        </div>
      </div>
    </div>

    <div class="card-box mb-5 p-5">
      <div class="mb-4">
        <h2 class="text-lg font-bold">价格时序数据库</h2>
        <p class="mt-1 text-sm text-slate-500">
          聚合 SKU 每次抓取的标价、到手价、促销语，并自动计算促销公式与历史极值。
        </p>
        <div
          v-if="routeFilterHint"
          class="mt-3 rounded-lg border border-amber-100 bg-amber-50 px-4 py-2 text-sm text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-300"
        >
          {{ routeFilterHint }}
        </div>
      </div>

      <ElForm ref="queryFormRef" :inline="true" :model="queryForm" class="price-filter">
        <ElFormItem label="关键词" prop="keyword">
          <ElInput
            v-model="queryForm.keyword"
            clearable
            placeholder="搜索 SKU / 商品名称"
            style="width: 240px"
          />
        </ElFormItem>
        <ElFormItem label="平台" prop="platform">
          <ElSelect
            v-model="queryForm.platform"
            clearable
            placeholder="全部平台"
            style="width: 160px"
          >
            <ElOption
              v-for="item in platformOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="状态" prop="status">
          <ElSelect v-model="queryForm.status" style="width: 140px">
            <ElOption
              v-for="item in statusOptions"
              :key="`${item.value}`"
              :label="item.label"
              :value="item.value"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="handleSearch">查询</ElButton>
          <ElButton @click="handleReset">重置</ElButton>
        </ElFormItem>
      </ElForm>
    </div>

    <div class="content-grid grid gap-5 2xl:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <div class="card-box min-w-0 overflow-hidden p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <div class="text-base font-semibold text-slate-900 dark:text-slate-100">SKU 价格轨迹列表</div>
            <div class="mt-1 text-sm text-slate-500">
              点击任一 SKU 查看完整时间轴和促销模型拆解。
            </div>
          </div>
          <ElTag effect="dark" round type="info">当前 {{ tableData.length }} 条</ElTag>
        </div>

        <ElTable
          v-loading="loading"
          :current-row-key="selectedProductId"
          :data="tableData"
          border
          highlight-current-row
          row-key="id"
          stripe
          @row-click="handleRowClick"
        >
          <ElTableColumn label="商品" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="product-cell">
                <img
                  v-if="row.mainImageUrl"
                  :src="row.mainImageUrl"
                  alt="product"
                  class="product-image"
                />
                <div class="min-w-0">
                  <div class="truncate font-medium text-slate-900 dark:text-slate-100">{{ row.productName }}</div>
                  <div class="mt-1 text-xs text-slate-500">{{ row.skuId }}</div>
                  <div class="mt-1 text-xs text-slate-400">{{ row.shopName || '-' }}</div>
                </div>
              </div>
            </template>
          </ElTableColumn>
          <ElTableColumn label="当前价" min-width="90">
            <template #default="{ row }">
              <span class="font-semibold text-emerald-600">
                {{ hasPriceHistory(row) ? formatCurrency(row.currentPrice) : '暂无历史价格' }}
              </span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="历史低价" min-width="90">
            <template #default="{ row }">
              <span class="font-medium text-rose-600">
                {{ hasPriceHistory(row) ? formatCurrency(row.lowestPrice) : '暂无历史价格' }}
              </span>
            </template>
          </ElTableColumn>
          <ElTableColumn label="均价" min-width="90">
            <template #default="{ row }">
              {{ hasPriceHistory(row) ? formatCurrency(row.averagePrice) : '--' }}
            </template>
          </ElTableColumn>
          <ElTableColumn label="采样数" min-width="90" prop="captureCount" />
          <ElTableColumn label="最近促销语" min-width="170" show-overflow-tooltip>
            <template #default="{ row }">
              <ElTag effect="plain" round type="warning">
                {{ hasPriceHistory(row) ? row.recentPromoText || '日常价' : '暂无历史价格' }}
              </ElTag>
            </template>
          </ElTableColumn>
        </ElTable>

        <div class="mt-5 flex justify-end">
          <ElPagination
            :current-page="queryForm.page"
            :page-size="queryForm.pageSize"
            :page-sizes="[8, 12, 16, 20]"
            :total="total"
            background
            layout="total, sizes, prev, pager, next"
            @current-change="handlePageChange"
            @size-change="handlePageSizeChange"
          />
        </div>
      </div>

      <div class="detail-stack min-w-0 grid gap-5">
        <div class="card-box p-5">
          <ElSkeleton :loading="detailLoading" animated>
            <template #template>
              <div class="h-[120px] rounded-2xl bg-slate-100"></div>
            </template>
            <template #default>
              <template v-if="detail && selectedProduct">
                <div class="detail-hero">
                  <div class="min-w-0">
                    <div class="text-xs uppercase tracking-[0.24em] text-slate-400">
                      {{ selectedProduct.platform }}
                    </div>
                    <div class="mt-2 text-xl font-semibold text-slate-900 dark:text-slate-100">
                      {{ detail.product.productName }}
                    </div>
                    <div class="mt-2 text-sm text-slate-500">
                      {{ detail.product.skuId }} · {{ detail.product.brandName || '未标记品牌' }}
                    </div>
                    <div
                      v-if="detail.timeline.length === 0"
                      class="mt-3 text-sm font-medium text-amber-600"
                    >
                      暂无历史价格，等待后续抓取或导入快照。
                    </div>
                  </div>
                  <div class="detail-price-pill">
                    <span>当前到手</span>
                    <strong>
                      {{
                        detail.timeline.length > 0
                          ? formatCurrency(detail.priceExtremes.currentPrice)
                          : '--'
                      }}
                    </strong>
                  </div>
                </div>
              </template>
              <ElEmpty v-else description="暂无历史价格" />
            </template>
          </ElSkeleton>
        </div>

        <div class="card-box p-5">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <div class="text-base font-semibold text-slate-900 dark:text-slate-100">历史轨迹</div>
              <div class="mt-1 text-sm text-slate-500">
                标价和到手价双线对比，低价点自动高亮。
              </div>
            </div>
          </div>
          <ElSkeleton :loading="detailLoading" animated>
            <template #template>
              <div class="h-[320px] rounded-2xl bg-slate-100"></div>
            </template>
            <template #default>
              <EchartsUI ref="timelineChartRef" class="h-[320px] w-full" />
            </template>
          </ElSkeleton>
        </div>

        <div class="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          <div class="extreme-card">
            <span>历史最低价</span>
            <strong>
              {{
                detail && detail.timeline.length > 0
                  ? formatCurrency(detail.priceExtremes.lowestPrice)
                  : '--'
              }}
            </strong>
            <small>{{ detail?.priceExtremes.lowestPriceAt || '—' }}</small>
          </div>
          <div class="extreme-card">
            <span>历史最高价</span>
            <strong>
              {{
                detail && detail.timeline.length > 0
                  ? formatCurrency(detail.priceExtremes.highestPrice)
                  : '--'
              }}
            </strong>
            <small>{{ detail?.priceExtremes.highestPriceAt || '—' }}</small>
          </div>
          <div class="extreme-card">
            <span>历史均价</span>
            <strong>
              {{
                detail && detail.timeline.length > 0
                  ? formatCurrency(detail.priceExtremes.averagePrice)
                  : '--'
              }}
            </strong>
            <small>
              波动区间
              {{
                detail && detail.timeline.length > 0
                  ? formatCurrency(detail.priceExtremes.priceSpan)
                  : '--'
              }}
            </small>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <div
            v-for="item in priceInsightCards"
            :key="item.label"
            class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900"
          >
            <div class="mb-3 flex items-center justify-between gap-2">
              <span class="text-sm font-semibold text-slate-600 dark:text-slate-300">{{ item.label }}</span>
              <ElTag :type="item.tone" size="small">分析</ElTag>
            </div>
            <div class="text-sm font-semibold text-slate-900 dark:text-slate-100">{{ item.value }}</div>
          </div>
        </div>

        <div class="card-box p-5">
          <div class="mb-4">
            <div class="text-base font-semibold text-slate-900 dark:text-slate-100">促销模型记录</div>
            <div class="mt-1 text-sm text-slate-500">
              自动拆解满减、优惠券、平台补贴，并拼出可读公式。
            </div>
          </div>

          <ElTable
            v-if="detail && detail.promotionRecords.length > 0"
            :data="detail.promotionRecords"
            border
            max-height="360"
            stripe
          >
            <ElTableColumn label="抓取时间" min-width="160" prop="capturedAt" />
            <ElTableColumn label="促销语" min-width="140" prop="promoText" />
            <ElTableColumn label="标价" min-width="100">
              <template #default="{ row }">{{ formatCurrency(row.listPrice) }}</template>
            </ElTableColumn>
            <ElTableColumn label="到手价" min-width="100">
              <template #default="{ row }">
                <span class="font-semibold text-emerald-600">
                  {{ formatCurrency(row.finalPrice) }}
                </span>
              </template>
            </ElTableColumn>
            <ElTableColumn label="优惠公式" min-width="240" prop="formula" show-overflow-tooltip />
          </ElTable>
          <ElEmpty
            v-else
            :description="detail?.timeline.length === 0 ? '暂无历史价格' : '暂无促销记录'"
          >
            <ElButton type="primary" @click="handleSearch">
              刷新价格数据
            </ElButton>
          </ElEmpty>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.metric-card {
  position: relative;
}

.metric-card__glow {
  inset: 0;
  opacity: 0.9;
  position: absolute;
}

.product-cell {
  align-items: center;
  display: flex;
  gap: 12px;
}

.product-image {
  border-radius: 16px;
  flex-shrink: 0;
  height: 52px;
  object-fit: cover;
  width: 52px;
}

.detail-hero {
  align-items: center;
  background:
    radial-gradient(circle at top left, rgb(14 165 233 / 0.18), transparent 38%),
    linear-gradient(135deg, #0f172a, #1e293b);
  border-radius: 24px;
  color: #fff;
  display: flex;
  gap: 20px;
  justify-content: space-between;
  padding: 24px;
}

.detail-price-pill {
  align-items: flex-end;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 120px;
}

.detail-price-pill span {
  color: rgb(226 232 240 / 0.86);
  font-size: 12px;
}

.detail-price-pill strong {
  font-size: 28px;
  line-height: 1;
}

.extreme-card {
  background:
    linear-gradient(180deg, rgb(255 255 255 / 0.96), rgb(241 245 249 / 0.96)),
    linear-gradient(135deg, rgb(14 165 233 / 0.08), rgb(249 115 22 / 0.12));
  border: 1px solid rgb(226 232 240);
  border-radius: 24px;
  box-shadow: 0 10px 30px rgb(15 23 42 / 0.06);
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 144px;
  padding: 22px;
}

.extreme-card span {
  color: #64748b;
  font-size: 13px;
}

.extreme-card strong {
  color: #0f172a;
  font-size: 28px;
  font-weight: 600;
  line-height: 1.1;
}

.extreme-card small {
  color: #94a3b8;
  font-size: 12px;
}

.dark .extreme-card {
  background:
    linear-gradient(180deg, rgb(15 23 42 / 0.96), rgb(2 6 23 / 0.96)),
    linear-gradient(135deg, rgb(14 165 233 / 0.12), rgb(249 115 22 / 0.1));
  border-color: rgb(30 41 59);
  box-shadow: none;
}

.dark .extreme-card strong {
  color: #f8fafc;
}
</style>
