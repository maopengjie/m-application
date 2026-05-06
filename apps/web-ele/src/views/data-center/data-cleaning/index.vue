<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { EchartsUIType } from '@vben/plugins/echarts';
import {
  ElButton,
  ElDatePicker,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElNotification,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
} from 'element-plus';
import { usePreferences } from '@vben/preferences';
import { EchartsUI, useEcharts } from '@vben/plugins/echarts';
import { useUserStore } from '@vben/stores';

import {
  buildAnomaliesExportUrl,
  getAnomalyContextApi,
  getAuditLogsApi,
  getEtlLogsApi,
  getAnomaliesApi,
  getEfficiencyApi,
  getCleaningStatsApi,
  verifyAnomalyApi,
  retryAnomalyScrapeApi,
  type AnomalyContext,
  type EtlLog,
  type AnomalyAlert,
  type EfficiencyRecord,
  type CleaningStats,
} from '#/api/data-cleaning';

const route = useRoute();
const router = useRouter();
const activeTab = ref(route.query.tab === 'anomalies' ? 'anomalies' : 'logs');
const { isDark } = usePreferences();
const userStore = useUserStore();
const canGovernData = computed(() =>
  userStore.userRoles.some((role) => ['admin', 'super'].includes(role)),
);

// --- Summary Stats ---
const stats = reactive<CleaningStats>({
  totalCleaned: 0,
  totalAnomalies: 0,
  avgResponseTime: 0,
  successRate: 0,
});

const metricCards = computed(() => [
  {
    label: '已清洗商品名',
    value: stats.totalCleaned,
    suffix: '件',
    accent: isDark.value ? 'from-blue-500/10 to-indigo-500/0' : 'from-blue-500/20 to-indigo-500/5',
    color: 'text-blue-600',
  },
  {
    label: '检测到异常',
    value: stats.totalAnomalies,
    suffix: '次',
    accent: isDark.value ? 'from-rose-500/10 to-orange-500/0' : 'from-rose-500/20 to-orange-500/5',
    color: 'text-rose-600',
  },
  {
    label: '平均响应耗时',
    value: stats.avgResponseTime,
    suffix: 'ms',
    accent: isDark.value ? 'from-emerald-500/10 to-teal-500/0' : 'from-emerald-500/20 to-teal-500/5',
    color: 'text-emerald-600',
  },
  {
    label: '抓取成功率',
    value: stats.successRate,
    suffix: '%',
    accent: isDark.value ? 'from-violet-500/10 to-purple-500/0' : 'from-violet-500/20 to-purple-500/5',
    color: 'text-violet-600',
  },
]);

// --- ETL Logs ---
const etlLogs = ref<EtlLog[]>([]);
const auditLogs = ref<EtlLog[]>([]);
const etlLoading = ref(false);

async function loadEtlLogs() {
  etlLoading.value = true;
  try {
    const [logs, audits] = await Promise.all([
      getEtlLogsApi(),
      getAuditLogsApi({ limit: 30 }),
    ]);
    etlLogs.value = logs;
    auditLogs.value = audits;
  } catch (error) {
    ElMessage.error('加载清洗日志失败');
  } finally {
    etlLoading.value = false;
  }
}

// --- Anomaly Alerts ---
const anomalies = ref<AnomalyAlert[]>([]);
const anomalyLoading = ref(false);
const anomalyFilter = ref<'all' | 'pending' | 'verified'>('all');
const anomalyDateRange = ref<[string, string] | []>([]);
const anomalyType = ref('');
const anomalyPlatform = ref('');
const anomalySkuKeyword = ref('');
const verifyDialogVisible = ref(false);
const contextDialogVisible = ref(false);
const verifySubmitting = ref(false);
const retryScrapeSubmitting = ref(false);
const contextLoading = ref(false);
const selectedAnomaly = ref<AnomalyAlert | null>(null);
const anomalyContext = ref<AnomalyContext | null>(null);
const verifyForm = reactive({
  verificationResult: '',
});
const verifyStatus = ref<'ignored' | 'review' | 'retry' | 'verified'>('verified');

const verificationStatusOptions = [
  { label: '已核实', value: 'verified' },
  { label: '已忽略', value: 'ignored' },
  { label: '已重抓', value: 'retry' },
  { label: '待复查', value: 'review' },
] as const;

async function loadAnomalies() {
  anomalyLoading.value = true;
  try {
    anomalies.value = await getAnomaliesApi({
      alert_type: anomalyType.value || undefined,
      end_at:
        anomalyDateRange.value.length === 2
          ? anomalyDateRange.value[1]
          : undefined,
      is_verified:
        anomalyFilter.value === 'all'
          ? undefined
          : anomalyFilter.value === 'verified'
            ? 1
            : 0,
      platform: anomalyPlatform.value || undefined,
      sku_id: anomalySkuKeyword.value || undefined,
      start_at:
        anomalyDateRange.value.length === 2
          ? anomalyDateRange.value[0]
          : undefined,
    });
  } catch (error) {
    ElMessage.error('加载异常记录失败');
  } finally {
    anomalyLoading.value = false;
  }
}

function handleAnomalyFilterChange() {
  void router.replace({
    query: {
      ...route.query,
      status: anomalyFilter.value === 'all' ? undefined : anomalyFilter.value,
      tab: 'anomalies',
    },
  });
  void loadAnomalies();
}

function handleAnomalyDateRangeChange() {
  void loadAnomalies();
}

function handleAnomalyQueryChange() {
  void loadAnomalies();
}

function formatAnomalyType(alertType: string) {
  if (alertType === 'PRICE_BUG') return '价格异常';
  if (alertType === 'STOCK_BUG') return '库存异常';
  if (alertType === 'DATA_MISSING') return '数据缺失';
  if (alertType === 'SCRAPE_FAILURE') return '抓取失败';
  return alertType;
}

function getAnomalyTagType(alertType: string) {
  if (alertType === 'PRICE_BUG') return 'danger';
  if (alertType === 'SCRAPE_FAILURE') return 'warning';
  return 'info';
}

function formatRunStatus(status: string) {
  if (status === 'SUCCESS') return 'success';
  if (status === 'PARTIAL_SUCCESS') return 'warning';
  if (status === 'FAILED') return 'danger';
  if (status === 'TIMEOUT') return 'danger';
  if (status === 'RUNNING') return 'primary';
  return 'info';
}

function formatRunStatusLabel(status: string) {
  if (status === 'SUCCESS') return '成功';
  if (status === 'PARTIAL_SUCCESS') return '部分成功';
  if (status === 'FAILED') return '失败';
  if (status === 'TIMEOUT') return '超时';
  if (status === 'RUNNING') return '执行中';
  return '排队中';
}

function openVerifyDialog(row: AnomalyAlert) {
  if (!canGovernData.value) {
    ElMessage.warning('当前角色仅可查看异常，无法核验');
    return;
  }
  selectedAnomaly.value = row;
  verifyStatus.value = parseVerificationStatus(row.verificationResult);
  verifyForm.verificationResult = stripVerificationStatus(row.verificationResult);
  verifyDialogVisible.value = true;
}

function applyRouteQuery() {
  if (route.query.tab === 'anomalies') {
    activeTab.value = 'anomalies';
  }
  if (route.query.status === 'pending' || route.query.status === 'verified') {
    anomalyFilter.value = route.query.status;
  }
}

function formatVerificationStatus(row: AnomalyAlert) {
  if (!row.isVerified) {
    return '待处理';
  }
  const status = parseVerificationStatus(row.verificationResult);
  return verificationStatusOptions.find((item) => item.value === status)?.label ?? '已核实';
}

function getVerificationTagType(row: AnomalyAlert) {
  if (!row.isVerified) return 'info';
  const status = parseVerificationStatus(row.verificationResult);
  if (status === 'ignored') return 'warning';
  if (status === 'review') return 'primary';
  if (status === 'retry') return 'success';
  return 'success';
}

function parseVerificationStatus(value?: string) {
  const matched = value?.match(/^状态：(已核实|已忽略|已重抓|待复查)；/);
  if (!matched) return 'verified';
  if (matched[1] === '已忽略') return 'ignored';
  if (matched[1] === '已重抓') return 'retry';
  if (matched[1] === '待复查') return 'review';
  return 'verified';
}

function stripVerificationStatus(value?: string) {
  return value?.replace(/^状态：(已核实|已忽略|已重抓|待复查)；/, '') ?? '';
}

function buildVerificationResult(status: typeof verifyStatus.value, note: string) {
  const label = verificationStatusOptions.find((item) => item.value === status)?.label ?? '已核实';
  return `状态：${label}；${note || label}`;
}

async function openContextDialog(row: AnomalyAlert) {
  selectedAnomaly.value = row;
  contextDialogVisible.value = true;
  contextLoading.value = true;
  anomalyContext.value = null;
  try {
    anomalyContext.value = await getAnomalyContextApi(row.id);
  } catch (error) {
    ElMessage.error('加载异常上下文失败');
    contextDialogVisible.value = false;
  } finally {
    contextLoading.value = false;
  }
}

async function submitVerification() {
  if (!canGovernData.value) {
    ElMessage.warning('当前角色无异常核验权限');
    return;
  }
  if (!selectedAnomaly.value) {
    return;
  }
  const anomaly = selectedAnomaly.value;
  verifySubmitting.value = true;
  try {
    const updated = await verifyAnomalyApi(anomaly.id, {
      isVerified: 1,
      verificationResult: buildVerificationResult(
        verifyStatus.value,
        verifyForm.verificationResult,
      ),
    });
    ElNotification({
      duration: 6000,
      message: `异常 #${updated.id} 已标记为已核实，处理结论会保留在异常队列和导出报表中。`,
      title: '核验结果已保存',
      type: 'success',
    });
    verifyDialogVisible.value = false;
    await Promise.all([loadAnomalies(), loadStats()]);
  } catch (error) {
    ElMessage.error('更新核验结果失败');
  } finally {
    verifySubmitting.value = false;
  }
}

function canRetryAnomaly(row: AnomalyAlert | null) {
  return row?.alertType === 'SCRAPE_FAILURE' || row?.alertType === 'DATA_MISSING';
}

async function retryAnomalyScrape(row?: AnomalyAlert | null) {
  const target = row || selectedAnomaly.value;
  if (!canGovernData.value) {
    ElMessage.warning('当前角色无异常重抓权限');
    return;
  }
  if (!target || !canRetryAnomaly(target)) {
    return;
  }

  retryScrapeSubmitting.value = true;
  try {
    const result = await retryAnomalyScrapeApi(target.id);
    await verifyAnomalyApi(target.id, {
      isVerified: 1,
      verificationResult: buildVerificationResult(
        'retry',
        `已创建重抓任务 #${result.runId}，等待抓取结果回写。`,
      ),
    });
    ElNotification({
      duration: 7000,
      message: `异常 #${result.anomalyId} 已创建重抓任务 #${result.runId}。请到“商品库”的抓取任务列表查看排队、执行和失败项。`,
      onClick: () => {
        void router.push({
          path: '/data-center/sku-repository',
          query: { runId: String(result.runId) },
        });
      },
      title: '异常重抓已创建',
      type: 'success',
    });
    contextDialogVisible.value = false;
    await Promise.all([loadAnomalies(), loadStats()]);
  } catch (error) {
    console.error('Failed to retry anomaly scrape:', error);
    ElMessage.error('投递重抓任务失败');
  } finally {
    retryScrapeSubmitting.value = false;
  }
}

function exportAnomaliesReport() {
  if (anomalies.value.length === 0) {
    ElMessage.warning('当前没有可导出的异常记录');
    return;
  }

  const link = document.createElement('a');
  link.href = buildAnomaliesExportUrl({
    alertType: anomalyType.value || undefined,
    endAt: anomalyDateRange.value.length === 2 ? anomalyDateRange.value[1] : undefined,
    isVerified:
      anomalyFilter.value === 'all'
        ? undefined
        : anomalyFilter.value === 'verified'
          ? 1
          : 0,
    platform: anomalyPlatform.value || undefined,
    skuId: anomalySkuKeyword.value || undefined,
    startAt: anomalyDateRange.value.length === 2 ? anomalyDateRange.value[0] : undefined,
  });
  link.download = '';
  document.body.append(link);
  link.click();
  link.remove();
}

// --- Efficiency Chart ---
const efficiencyData = ref<EfficiencyRecord[]>([]);
const chartRef = ref<EchartsUIType>();
const { renderEcharts, resize } = useEcharts(chartRef);

async function loadEfficiency() {
  try {
    const data = await getEfficiencyApi();
    if (Array.isArray(data)) {
      efficiencyData.value = data.reverse(); // Time order for chart
      updateChart();
    } else {
      console.warn('Efficiency data is not an array:', data);
    }
  } catch (error) {
    console.error('Failed to load efficiency data:', error);
  }
}

function updateChart() {
  const times = efficiencyData.value.map(d => new Date(d.capturedAt).toLocaleTimeString());
  const values = efficiencyData.value.map(d => d.responseTimeMs);

  renderEcharts({
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark.value ? '#1e293b' : '#fff',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#f1f5f9' : '#1e293b' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: times,
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b' },
    },
    yAxis: {
      type: 'value',
      name: '响应耗时 (ms)',
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b' },
      splitLine: { lineStyle: { type: 'dashed', color: isDark.value ? '#334155' : '#f1f5f9' } },
    },
    series: [
      {
        name: 'Response Time',
        type: 'line',
        smooth: true,
        data: values,
        itemStyle: { color: '#3b82f6' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0)' }
            ]
          }
        },
      },
    ],
  });
}

// --- General ---
async function loadStats() {
  try {
    const res = await getCleaningStatsApi();
    Object.assign(stats, res);
  } catch (error) {
    console.error('Failed to load stats');
  }
}

onMounted(() => {
  applyRouteQuery();
  loadStats();
  loadEtlLogs();
  loadAnomalies();
  loadEfficiency();
});

watch(
  () => [route.query.status, route.query.tab],
  () => {
    applyRouteQuery();
    if (activeTab.value === 'anomalies') {
      void loadAnomalies();
    }
  },
);

watch(isDark, () => {
  if (activeTab.value === 'efficiency') updateChart();
});

function handleTabChange(tab: any) {
  if (tab === 'efficiency') {
    setTimeout(() => {
      resize();
      updateChart();
    }, 100);
  }
}
</script>

<template>
  <div class="data-cleaning-page p-6">
    <!-- Header -->
    <div class="mb-8 flex items-end justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">数据清洗与日志监控</h1>
        <p class="mt-2 text-base text-slate-500 dark:text-slate-400">
          监控 ETL 流程，处理商品名杂质，拦截价格异常并追踪抓取效能。
        </p>
      </div>
      <div class="flex items-center gap-3">
        <div class="status-badge bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-500/10 dark:text-emerald-400 dark:border-emerald-500/20">
          <div class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse mr-2"></div>
          清洗引擎运行中
        </div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="mb-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
      <div
        v-for="item in metricCards"
        :key="item.label"
        class="metric-card relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
      >
        <div class="metric-card__glow absolute inset-0 bg-gradient-to-br opacity-60 dark:opacity-20" :class="item.accent"></div>
        <div class="relative z-10">
          <div class="text-sm font-medium text-slate-500 dark:text-slate-400">{{ item.label }}</div>
          <div class="mt-4 flex items-baseline gap-1">
            <span class="text-3xl font-black tracking-tight" :class="item.color">{{ item.value }}</span>
            <span class="text-sm font-semibold text-slate-400">{{ item.suffix }}</span>
          </div>
        </div>
      </div>
    </div>

    <ElTabs v-model="activeTab" class="custom-tabs" @tab-change="handleTabChange">
      <!-- Cleaning Logs -->
      <ElTabPane label="自动化清洗记录" name="logs">
        <div class="grid gap-5">
        <div class="card-box dark:bg-slate-900 dark:border-slate-800">
          <div class="card-header border-b border-slate-100 p-6 dark:border-slate-800">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">过滤广告语日志</h3>
              <ElButton link type="primary" @click="loadEtlLogs">刷新日志</ElButton>
            </div>
          </div>
          <div class="p-6">
            <ElTable v-loading="etlLoading" :data="etlLogs" border stripe class="premium-table">
              <ElTableColumn label="商品ID / 平台" width="180">
                <template #default="{ row }">
                  <div class="flex flex-col">
                    <span class="font-mono text-xs font-bold text-slate-700 dark:text-slate-300">{{ row.skuId }}</span>
                    <ElTag size="small" effect="plain" class="mt-1 w-fit">{{ row.platform?.toUpperCase() }}</ElTag>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="清洗前后对比" min-width="400">
                <template #default="{ row }">
                  <div class="flex flex-col gap-2 py-2">
                    <div class="flex items-start gap-2">
                      <ElTag size="small" type="info" effect="dark" class="mt-0.5 rounded-md">原</ElTag>
                      <span class="text-sm text-slate-400 line-through decoration-slate-300">{{ row.originalValue }}</span>
                    </div>
                    <div class="flex items-start gap-2">
                      <ElTag size="small" type="success" effect="dark" class="mt-0.5 rounded-md">新</ElTag>
                      <span class="text-sm font-bold text-slate-800 dark:text-slate-200">{{ row.cleanedValue }}</span>
                    </div>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="命中的广告模式" min-width="200">
                <template #default="{ row }">
                  <div class="flex flex-wrap gap-1">
                    <ElTag 
                      v-for="slogan in (row.message?.replace('Filtered slogans: ', '').split(', ') || [])" 
                      :key="slogan"
                      size="small"
                      type="warning"
                      effect="plain"
                      class="rounded-full"
                    >
                      {{ slogan }}
                    </ElTag>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="处理时间" prop="createdAt" width="180" align="center">
                <template #default="{ row }">
                  <span class="text-xs text-slate-500">{{ new Date(row.createdAt).toLocaleString() }}</span>
                </template>
              </ElTableColumn>
            </ElTable>
          </div>
        </div>
        <div class="card-box dark:bg-slate-900 dark:border-slate-800">
          <div class="card-header border-b border-slate-100 p-6 dark:border-slate-800">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">操作审计</h3>
              <ElButton link type="primary" @click="loadEtlLogs">刷新审计</ElButton>
            </div>
          </div>
          <div class="p-6">
            <ElTable :data="auditLogs" border stripe class="premium-table">
              <ElTableColumn label="操作者" min-width="140" prop="originalValue" />
              <ElTableColumn label="动作" min-width="160" prop="fieldName" />
              <ElTableColumn label="对象" min-width="160">
                <template #default="{ row }">
                  {{ row.skuId || row.productId || '-' }}
                </template>
              </ElTableColumn>
              <ElTableColumn label="详情" min-width="320" prop="cleanedValue" />
              <ElTableColumn label="时间" min-width="180" prop="createdAt" />
            </ElTable>
            <ElEmpty
              v-if="auditLogs.length === 0"
              description="暂无操作审计记录"
              :image-size="72"
            />
          </div>
        </div>
        </div>
      </ElTabPane>

      <!-- Anomaly Alerts -->
      <ElTabPane label="异常拦截与核验" name="anomalies">
        <div class="card-box dark:bg-slate-900 dark:border-slate-800">
          <div class="card-header border-b border-slate-100 p-6 dark:border-slate-800">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">价格异常拦截队列</h3>
              <div class="flex gap-2">
                <ElInput
                  v-model="anomalySkuKeyword"
                  clearable
                  placeholder="搜索 SKU"
                  style="width: 180px"
                  @clear="handleAnomalyQueryChange"
                  @keyup.enter="handleAnomalyQueryChange"
                />
                <ElSelect
                  v-model="anomalyPlatform"
                  clearable
                  placeholder="全部平台"
                  style="width: 140px"
                  @change="handleAnomalyQueryChange"
                >
                  <ElOption label="京东" value="jd" />
                  <ElOption label="天猫" value="tmall" />
                  <ElOption label="拼多多" value="pdd" />
                </ElSelect>
                <ElSelect
                  v-model="anomalyType"
                  clearable
                  placeholder="全部类型"
                  style="width: 160px"
                  @change="handleAnomalyQueryChange"
                >
                  <ElOption label="价格异常" value="PRICE_BUG" />
                  <ElOption label="库存异常" value="STOCK_BUG" />
                  <ElOption label="数据缺失" value="DATA_MISSING" />
                  <ElOption label="抓取失败" value="SCRAPE_FAILURE" />
                </ElSelect>
                <ElDatePicker
                  v-model="anomalyDateRange"
                  clearable
                  end-placeholder="结束时间"
                  range-separator="至"
                  start-placeholder="开始时间"
                  type="datetimerange"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  @change="handleAnomalyDateRangeChange"
                />
                <ElSelect
                  v-model="anomalyFilter"
                  style="width: 160px"
                  @change="handleAnomalyFilterChange"
                >
                  <ElOption label="全部异常" value="all" />
                  <ElOption label="待处理" value="pending" />
                  <ElOption label="已核实" value="verified" />
                </ElSelect>
                <ElButton
                  type="primary"
                  plain
                  class="premium-button"
                  @click="exportAnomaliesReport"
                >
                  导出异常报表
                </ElButton>
                <ElButton @click="loadAnomalies">刷新</ElButton>
              </div>
            </div>
          </div>
          <div class="p-6">
            <ElTable v-loading="anomalyLoading" :data="anomalies" border stripe class="premium-table">
              <ElTableColumn label="异常类型" width="120" align="center">
                <template #default="{ row }">
                  <ElTag :type="getAnomalyTagType(row.alertType)" effect="dark">
                    {{ formatAnomalyType(row.alertType) }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn label="原始 SKU" prop="skuId" width="150" />
              <ElTableColumn label="异常数值" width="120" align="center">
                <template #default="{ row }">
                  <span class="text-lg font-black text-rose-600">{{ row.alertValue }}</span>
                </template>
              </ElTableColumn>
              <ElTableColumn label="异常描述" prop="message" min-width="200" />
              <ElTableColumn label="核验状态" width="120" align="center">
                <template #default="{ row }">
                  <ElTag :type="getVerificationTagType(row)" effect="plain">
                    {{ formatVerificationStatus(row) }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn label="处理结果" min-width="200">
                <template #default="{ row }">
                  {{ stripVerificationStatus(row.verificationResult) || '-' }}
                </template>
              </ElTableColumn>
              <ElTableColumn label="操作" width="280" align="center" fixed="right">
                <template #default="{ row }">
                  <ElButton
                    link
                    type="primary"
                    class="font-bold"
                    :disabled="!canGovernData"
                    @click="openVerifyDialog(row)"
                  >
                    {{ row.isVerified ? '查看结果' : '立即核验' }}
                  </ElButton>
                  <ElButton
                    v-if="canRetryAnomaly(row)"
                    link
                    type="warning"
                    class="font-bold"
                    @click="openContextDialog(row)"
                  >
                    查看上下文
                  </ElButton>
                  <ElButton
                    v-if="canRetryAnomaly(row)"
                    link
                    type="success"
                    class="font-bold"
                    :loading="retryScrapeSubmitting"
                    :disabled="!canGovernData"
                    @click="retryAnomalyScrape(row)"
                  >
                    重新抓取
                  </ElButton>
                </template>
              </ElTableColumn>
            </ElTable>
          </div>
        </div>
      </ElTabPane>

      <!-- Efficiency -->
      <ElTabPane label="接口采集效率" name="efficiency">
        <div class="grid gap-6">
          <div class="card-box p-6 dark:bg-slate-900 dark:border-slate-800">
            <div class="mb-6 flex items-center justify-between">
              <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">JD 接口响应耗时趋势</h3>
              <div class="text-sm text-slate-400">最近 24 小时监控</div>
            </div>
            <EchartsUI ref="chartRef" class="h-[400px] w-full" />
          </div>

          <div class="card-box dark:bg-slate-900 dark:border-slate-800">
            <div class="border-b border-slate-100 p-6 dark:border-slate-800">
              <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">详细抓取日志</h3>
            </div>
            <div class="p-6">
              <ElTable :data="efficiencyData.slice().reverse()" border stripe height="300" class="premium-table">
                <ElTableColumn label="目标接口" prop="targetApi" min-width="200" />
                <ElTableColumn label="响应时间" prop="responseTimeMs" width="120" align="center">
                  <template #default="{ row }">
                    <span :class="row.responseTimeMs > 500 ? 'text-orange-500 font-bold' : 'text-emerald-500'">
                      {{ row.responseTimeMs }} ms
                    </span>
                  </template>
                </ElTableColumn>
                <ElTableColumn label="状态码" prop="statusCode" width="100" align="center">
                  <template #default="{ row }">
                    <ElTag :type="row.statusCode === 200 ? 'success' : 'danger'" size="small">
                      {{ row.statusCode }}
                    </ElTag>
                  </template>
                </ElTableColumn>
                <ElTableColumn label="抓取时间" prop="capturedAt" width="200" align="center">
                   <template #default="{ row }">
                    {{ new Date(row.capturedAt).toLocaleString() }}
                  </template>
                </ElTableColumn>
              </ElTable>
            </div>
          </div>
        </div>
      </ElTabPane>
    </ElTabs>

    <ElDialog
      v-model="verifyDialogVisible"
      :title="selectedAnomaly?.isVerified ? '核验结果' : '异常核验'"
      width="520px"
    >
      <div v-if="selectedAnomaly" class="space-y-4">
        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-800/60">
          <div><strong>SKU：</strong>{{ selectedAnomaly.skuId }}</div>
          <div class="mt-2"><strong>异常类型：</strong>{{ selectedAnomaly.alertType }}</div>
          <div class="mt-2"><strong>异常数值：</strong>{{ selectedAnomaly.alertValue }}</div>
          <div class="mt-2"><strong>异常描述：</strong>{{ selectedAnomaly.message || '—' }}</div>
        </div>

        <ElForm label-position="top">
          <ElFormItem label="处理状态">
            <ElSelect v-model="verifyStatus" style="width: 100%">
              <ElOption
                v-for="item in verificationStatusOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="核验结果">
            <ElInput
              v-model="verifyForm.verificationResult"
              :rows="4"
              type="textarea"
              placeholder="填写人工核验结论，例如：已确认是接口异常，已忽略本次预警"
            />
          </ElFormItem>
        </ElForm>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <ElButton @click="verifyDialogVisible = false">关闭</ElButton>
          <ElButton
            v-if="selectedAnomaly && !selectedAnomaly.isVerified"
            type="primary"
            :loading="verifySubmitting"
            :disabled="!canGovernData"
            @click="submitVerification"
          >
            提交核验
          </ElButton>
        </div>
      </template>
    </ElDialog>

    <ElDialog
      v-model="contextDialogVisible"
      title="异常上下文"
      width="760px"
    >
      <div v-loading="contextLoading">
        <div v-if="anomalyContext" class="space-y-4">
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-800/60">
            <div><strong>关联商品：</strong>{{ anomalyContext.productName || '未匹配到商品' }}</div>
            <div class="mt-2"><strong>商品ID：</strong>{{ anomalyContext.productId || '-' }}</div>
            <div class="mt-2">
              <strong>商品链接：</strong>
              <a
                v-if="anomalyContext.productUrl"
                :href="anomalyContext.productUrl"
                class="text-blue-500"
                rel="noreferrer"
                target="_blank"
              >
                {{ anomalyContext.productUrl }}
              </a>
              <span v-else>-</span>
            </div>
          </div>

          <div>
            <h4 class="mb-3 text-base font-bold text-slate-900 dark:text-slate-100">最近相关抓取任务</h4>
            <ElTable
              v-if="anomalyContext.recentRuns.length > 0"
              :data="anomalyContext.recentRuns"
              border
              max-height="320"
            >
              <ElTableColumn label="任务ID" min-width="90" prop="id" />
              <ElTableColumn label="任务类型" min-width="120">
                <template #default="{ row }">
                  {{ row.taskName === 'scrape_product' ? '单商品抓取' : '批量抓取' }}
                </template>
              </ElTableColumn>
              <ElTableColumn label="状态" min-width="120">
                <template #default="{ row }">
                  <ElTag :type="formatRunStatus(row.status)">
                    {{ formatRunStatusLabel(row.status) }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn label="执行结果" min-width="140">
                <template #default="{ row }">
                  成功 {{ row.successCount }} / 失败 {{ row.failureCount }}
                </template>
              </ElTableColumn>
              <ElTableColumn label="摘要" min-width="220" prop="summaryMessage" />
              <ElTableColumn label="创建时间" min-width="170" prop="createdAt" />
            </ElTable>
            <ElEmpty
              v-else
              description="暂无关联抓取任务"
              :image-size="72"
            />
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <ElButton @click="contextDialogVisible = false">关闭</ElButton>
          <ElButton
            v-if="canRetryAnomaly(selectedAnomaly)"
            :loading="retryScrapeSubmitting"
            :disabled="!canGovernData"
            type="primary"
            @click="retryAnomalyScrape(selectedAnomaly)"
          >
            重新抓取
          </ElButton>
        </div>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.data-cleaning-page {
  background:
    radial-gradient(circle at top left, var(--gradient-color-1, rgb(243 244 246 / 90%)), transparent 30%),
    radial-gradient(circle at bottom right, var(--gradient-color-2, rgb(219 234 254 / 50%)), transparent 30%),
    var(--page-bg, #f8fafc);
  min-height: 100%;
}

.dark .data-cleaning-page {
  --gradient-color-1: rgb(15 23 42 / 90%);
  --gradient-color-2: rgb(30 41 59 / 50%);
  --page-bg: #020617;
}

.status-badge {
  display: flex;
  align-items: center;
  padding: 6px 16px;
  border-radius: 20px;
  border-width: 1px;
  font-size: 13px;
  font-weight: 600;
}

.metric-card {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.metric-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px -8px rgb(0 0 0 / 10%);
}

.metric-card__glow {
  transition: opacity 0.3s ease;
}

.metric-card:hover .metric-card__glow {
  opacity: 0.9;
}

.card-box {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 32px;
  box-shadow: 0 4px 20px -5px rgb(0 0 0 / 5%);
  overflow: hidden;
}

.dark .card-box {
  background: #0f172a;
  border-color: #1e293b;
}

.custom-tabs :deep(.el-tabs__header) {
  margin-bottom: 32px;
  background: white;
  padding: 8px 24px;
  border-radius: 24px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 15px rgb(0 0 0 / 3%);
}

.dark .custom-tabs :deep(.el-tabs__header) {
  background: #0f172a;
  border-color: #1e293b;
}

.custom-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.custom-tabs :deep(.el-tabs__active-bar) {
  height: 4px;
  border-radius: 4px;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
}

.custom-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 700;
  color: #64748b;
  height: 52px;
  line-height: 52px;
}

.dark .custom-tabs :deep(.el-tabs__item) {
  color: #94a3b8;
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  color: #0f172a;
}

.dark .custom-tabs :deep(.el-tabs__item.is-active) {
  color: #f1f5f9;
}

.premium-table :deep(.el-table__header th) {
  background-color: #f8fafc;
  color: #475569;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.05em;
  padding: 16px 0;
}

.dark .premium-table :deep(.el-table__header th) {
  background-color: #1e293b;
  color: #94a3b8;
}

.premium-button {
  border-radius: 14px;
  font-weight: 700;
  padding: 10px 24px;
  transition: all 0.2s;
}

.premium-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
