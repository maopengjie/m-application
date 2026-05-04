<script lang="ts" setup>
import type { EchartsUIType } from '@vben/plugins/echarts';
import type { FormInstance } from 'element-plus';
import type {
  PriceTimeSeriesDetail,
  PriceTimeSeriesListItem,
  PriceTimeSeriesSummary,
} from '#/api';

import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';

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
  status: '' | -1 | 0 | 1;
}

const queryFormRef = ref<FormInstance>();
const timelineChartRef = ref<EchartsUIType>();
const timelineChart = useEcharts(timelineChartRef);

const loading = ref(false);
const detailLoading = ref(false);
const tableData = ref<PriceTimeSeriesListItem[]>([]);
const total = ref(0);
const summary = ref<PriceTimeSeriesSummary | null>(null);
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
  } finally {
    loading.value = false;
  }
}

async function loadDetail(productId: number) {
  selectedProductId.value = productId;
  detailLoading.value = true;
  try {
    detail.value = await getPriceTimeSeriesDetailApi(productId);
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
  await loadList();
});
</script>

<template>
  <div class="price-time-series-page p-5">
    <div class="metric-grid mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      <div
        v-for="item in metricCards"
        :key="item.label"
        class="metric-card overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
      >
        <div class="metric-card__glow bg-gradient-to-br" :class="item.accent" />
        <div class="relative z-10">
          <div class="text-sm text-slate-500">{{ item.label }}</div>
          <div class="mt-4 text-3xl font-semibold tracking-tight text-slate-900">
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
      </div>

      <el-form ref="queryFormRef" :inline="true" :model="queryForm" class="price-filter">
        <el-form-item label="关键词" prop="keyword">
          <el-input
            v-model="queryForm.keyword"
            clearable
            placeholder="搜索 SKU / 商品名称"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item label="平台" prop="platform">
          <el-select
            v-model="queryForm.platform"
            clearable
            placeholder="全部平台"
            style="width: 160px"
          >
            <el-option
              v-for="item in platformOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="queryForm.status" style="width: 140px">
            <el-option
              v-for="item in statusOptions"
              :key="`${item.value}`"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="content-grid grid gap-5 2xl:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)]">
      <div class="card-box min-w-0 overflow-hidden p-5">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <div class="text-base font-semibold text-slate-900">SKU 价格轨迹列表</div>
            <div class="mt-1 text-sm text-slate-500">
              点击任一 SKU 查看完整时间轴和促销模型拆解。
            </div>
          </div>
          <el-tag effect="dark" round type="info">当前 {{ tableData.length }} 条</el-tag>
        </div>

        <el-table
          v-loading="loading"
          :current-row-key="selectedProductId"
          :data="tableData"
          border
          highlight-current-row
          row-key="id"
          stripe
          @row-click="handleRowClick"
        >
          <el-table-column label="商品" min-width="220" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="product-cell">
                <img
                  v-if="row.mainImageUrl"
                  :src="row.mainImageUrl"
                  alt="product"
                  class="product-image"
                />
                <div class="min-w-0">
                  <div class="truncate font-medium text-slate-900">{{ row.productName }}</div>
                  <div class="mt-1 text-xs text-slate-500">{{ row.skuId }}</div>
                  <div class="mt-1 text-xs text-slate-400">{{ row.shopName || '-' }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="当前价" min-width="90">
            <template #default="{ row }">
              <span class="font-semibold text-emerald-600">
                {{ formatCurrency(row.currentPrice) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="历史低价" min-width="90">
            <template #default="{ row }">
              <span class="font-medium text-rose-600">
                {{ formatCurrency(row.lowestPrice) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="均价" min-width="90">
            <template #default="{ row }">
              {{ formatCurrency(row.averagePrice) }}
            </template>
          </el-table-column>
          <el-table-column label="采样数" min-width="90" prop="captureCount" />
          <el-table-column label="最近促销语" min-width="170" show-overflow-tooltip>
            <template #default="{ row }">
              <el-tag effect="plain" round type="warning">
                {{ row.recentPromoText || '日常价' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <div class="mt-5 flex justify-end">
          <el-pagination
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
          <el-skeleton :loading="detailLoading" animated>
            <template #template>
              <div class="h-[120px] rounded-2xl bg-slate-100" />
            </template>
            <template #default>
              <template v-if="detail && selectedProduct">
                <div class="detail-hero">
                  <div class="min-w-0">
                    <div class="text-xs uppercase tracking-[0.24em] text-slate-400">
                      {{ selectedProduct.platform }}
                    </div>
                    <div class="mt-2 text-xl font-semibold text-slate-900">
                      {{ detail.product.productName }}
                    </div>
                    <div class="mt-2 text-sm text-slate-500">
                      {{ detail.product.skuId }} · {{ detail.product.brandName || '未标记品牌' }}
                    </div>
                  </div>
                  <div class="detail-price-pill">
                    <span>当前到手</span>
                    <strong>{{ formatCurrency(detail.priceExtremes.currentPrice) }}</strong>
                  </div>
                </div>
              </template>
              <el-empty v-else description="暂无价格轨迹" />
            </template>
          </el-skeleton>
        </div>

        <div class="card-box p-5">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <div class="text-base font-semibold text-slate-900">历史轨迹</div>
              <div class="mt-1 text-sm text-slate-500">
                标价和到手价双线对比，低价点自动高亮。
              </div>
            </div>
          </div>
          <el-skeleton :loading="detailLoading" animated>
            <template #template>
              <div class="h-[320px] rounded-2xl bg-slate-100" />
            </template>
            <template #default>
              <EchartsUI ref="timelineChartRef" class="h-[320px] w-full" />
            </template>
          </el-skeleton>
        </div>

        <div class="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          <div class="extreme-card">
            <span>历史最低价</span>
            <strong>{{ detail ? formatCurrency(detail.priceExtremes.lowestPrice) : '--' }}</strong>
            <small>{{ detail?.priceExtremes.lowestPriceAt || '—' }}</small>
          </div>
          <div class="extreme-card">
            <span>历史最高价</span>
            <strong>{{ detail ? formatCurrency(detail.priceExtremes.highestPrice) : '--' }}</strong>
            <small>{{ detail?.priceExtremes.highestPriceAt || '—' }}</small>
          </div>
          <div class="extreme-card">
            <span>历史均价</span>
            <strong>{{ detail ? formatCurrency(detail.priceExtremes.averagePrice) : '--' }}</strong>
            <small>波动区间 {{ detail ? formatCurrency(detail.priceExtremes.priceSpan) : '--' }}</small>
          </div>
        </div>

        <div class="card-box p-5">
          <div class="mb-4">
            <div class="text-base font-semibold text-slate-900">促销模型记录</div>
            <div class="mt-1 text-sm text-slate-500">
              自动拆解满减、优惠券、平台补贴，并拼出可读公式。
            </div>
          </div>

          <el-table v-if="detail" :data="detail.promotionRecords" border max-height="360" stripe>
            <el-table-column label="抓取时间" min-width="160" prop="capturedAt" />
            <el-table-column label="促销语" min-width="140" prop="promoText" />
            <el-table-column label="标价" min-width="100">
              <template #default="{ row }">{{ formatCurrency(row.listPrice) }}</template>
            </el-table-column>
            <el-table-column label="到手价" min-width="100">
              <template #default="{ row }">
                <span class="font-semibold text-emerald-600">
                  {{ formatCurrency(row.finalPrice) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="优惠公式" min-width="240" prop="formula" show-overflow-tooltip />
          </el-table>
          <el-empty v-else description="暂无促销记录" />
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
</style>
