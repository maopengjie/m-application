<script lang="ts" setup>
import type { FormInstance } from 'element-plus';

import type {
  ScrapeTaskOverview,
  ScrapeTaskRun,
  SkuProductDetail,
  SkuProductListItem,
  SkuTag,
} from '#/api';

import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '@vben/stores';

import {
  ElButton,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDrawer,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElNotification,
  ElOption,
  ElPagination,
  ElSelect,
  ElSkeleton,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import {
  addSkuProductTagApi,
  getScrapeTaskRunDetailApi,
  getScrapeTaskOverviewApi,
  getScrapeTaskRunsApi,
  deleteSkuProductTagApi,
  getSkuProductDetailApi,
  getSkuProductsApi,
  getSkuTagsApi,
  retryScrapeTaskRunApi,
  triggerBatchScrapeApi,
  triggerScrapeProductApi,
} from '#/api';

const loading = ref(false);
const scrapeLoading = ref(false);
const scrapeSubmitting = ref(false);
const detailLoading = ref(false);
const drawerVisible = ref(false);
const editTagsVisible = ref(false);
const runDetailVisible = ref(false);
const tagSubmitting = ref(false);
const retrySubmitting = ref(false);
const singleScrapeSubmitting = ref(false);
const tableData = ref<SkuProductListItem[]>([]);
const total = ref(0);
const tags = ref<SkuTag[]>([]);
const scrapeRuns = ref<ScrapeTaskRun[]>([]);
const scrapeOverview = ref<null | ScrapeTaskOverview>(null);
const selectedProduct = ref<null | SkuProductDetail>(null);
const selectedRun = ref<null | ScrapeTaskRun>(null);
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const canOperateTasks = computed(() =>
  userStore.userRoles.some((role) => ['admin', 'super'].includes(role)),
);
const canGovernData = computed(() =>
  userStore.userRoles.some((role) => ['admin', 'super'].includes(role)),
);

const queryFormRef = ref<FormInstance>();
interface QueryFormState {
  brandName: string;
  keyword: string;
  page: number;
  pageSize: number;
  platform: string;
  status: -1 | 0 | 1 | '';
  tagCode: string;
}

const queryForm = reactive<QueryFormState>({
  brandName: '',
  keyword: '',
  page: 1,
  pageSize: 10,
  platform: '',
  status: 1,
  tagCode: '',
});

const tagForm = reactive({
  tagCode: '',
  tagValue: '',
});

const scrapeForm = reactive({
  limit: 20,
  platform: '',
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

const summary = computed(() => {
  const currentTags = tableData.value.flatMap((item) => item.tags);
  return {
    currentCount: tableData.value.length,
    selfOperatedCount: currentTags.filter((tag) => tag.tagCode === 'JD_SELF_OPERATED').length,
    totalCount: total.value,
    uniqueBrands: new Set(
      tableData.value.map((item) => item.brandName).filter(Boolean),
    ).size,
  };
});

function normalizeQuery() {
  return {
    brandName: queryForm.brandName || undefined,
    keyword: queryForm.keyword || undefined,
    page: queryForm.page,
    pageSize: queryForm.pageSize,
    platform: queryForm.platform || undefined,
    status: queryForm.status === '' ? undefined : queryForm.status,
    tagCode: queryForm.tagCode || undefined,
  };
}

async function loadProducts() {
  loading.value = true;
  try {
    const data = await getSkuProductsApi(normalizeQuery());
    tableData.value = data.items;
    total.value = data.total;
  } catch (error) {
    console.error('Failed to load products:', error);
    ElMessage.error('加载商品列表失败');
  } finally {
    loading.value = false;
  }
}

async function loadTags() {
  try {
    tags.value = await getSkuTagsApi();
  } catch (error) {
    console.error('Failed to load tags:', error);
  }
}

async function loadScrapeRuns() {
  scrapeLoading.value = true;
  try {
    const taskStatus = typeof route.query.taskStatus === 'string'
      ? route.query.taskStatus
      : '';
    const statusGroup = taskStatus === 'open'
      ? ['PENDING', 'RUNNING']
      : taskStatus === 'problem'
        ? ['FAILED', 'PARTIAL_SUCCESS', 'TIMEOUT']
        : [];
    const runRequests = statusGroup.length > 0
      ? statusGroup.map((status) =>
        getScrapeTaskRunsApi({
          limit: 8,
          platform: scrapeForm.platform || undefined,
          status,
        }),
      )
      : [
        getScrapeTaskRunsApi({
          limit: 8,
          platform: scrapeForm.platform || undefined,
        }),
      ];
    const [overview, ...runGroups] = await Promise.all([
      getScrapeTaskOverviewApi(),
      ...runRequests,
    ]);
    scrapeOverview.value = overview;
    scrapeRuns.value = runGroups
      .flat()
      .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
      .slice(0, 8);
  } catch (error) {
    console.error('Failed to load scrape runs:', error);
    ElMessage.error('加载抓取任务失败');
  } finally {
    scrapeLoading.value = false;
  }
}

async function openRunDetail(runId: number) {
  try {
    selectedRun.value = await getScrapeTaskRunDetailApi(runId);
    runDetailVisible.value = true;
  } catch (error) {
    console.error('Failed to load scrape run detail:', error);
    ElMessage.error('加载任务详情失败');
  }
}

async function openRunDetailFromRoute() {
  const runId = Number(route.query.runId);
  if (!Number.isFinite(runId) || runId <= 0) {
    return;
  }
  await openRunDetail(runId);
}

async function retrySelectedRun() {
  if (!selectedRun.value) {
    return;
  }
  retrySubmitting.value = true;
  try {
    const result = await retryScrapeTaskRunApi(selectedRun.value.id);
    notifyScrapeRunCreated({
      message: `已基于问题任务 #${result.previousRunId} 创建重试任务 #${result.run.id}，可在最近任务列表查看执行状态。`,
      runId: result.run.id,
      title: '重试任务已创建',
    });
    runDetailVisible.value = false;
    await loadScrapeRuns();
  } catch (error) {
    console.error('Failed to retry scrape run:', error);
    ElMessage.error('投递重试任务失败');
  } finally {
    retrySubmitting.value = false;
  }
}

async function openDetail(productId: number) {
  drawerVisible.value = true;
  detailLoading.value = true;
  selectedProduct.value = null;
  try {
    selectedProduct.value = await getSkuProductDetailApi(productId);
  } catch (error) {
    console.error('Failed to load product detail:', error);
    ElMessage.error('加载商品详情失败');
  } finally {
    detailLoading.value = false;
  }
}

function openTagEditor() {
  if (!selectedProduct.value) {
    return;
  }
  tagForm.tagCode = '';
  tagForm.tagValue = '';
  editTagsVisible.value = true;
}

async function triggerSelectedProductScrape() {
  if (!selectedProduct.value?.productUrl) {
    ElMessage.warning('当前商品没有可抓取链接');
    return;
  }

  singleScrapeSubmitting.value = true;
  try {
    const result = await triggerScrapeProductApi(selectedProduct.value.productUrl);
    notifyScrapeRunCreated({
      message: `任务 #${result.run.id} 已进入队列，将重抓当前商品并回写价格与异常状态。`,
      runId: result.run.id,
      title: '单商品抓取已创建',
    });
    await loadScrapeRuns();
  } catch (error) {
    console.error('Failed to trigger single scrape:', error);
    ElMessage.error('投递单商品抓取失败');
  } finally {
    singleScrapeSubmitting.value = false;
  }
}

async function triggerBatchScrape() {
  if (!canOperateTasks.value) {
    ElMessage.warning('当前角色无抓取任务配置权限');
    return;
  }
  scrapeSubmitting.value = true;
  try {
    const result = await triggerBatchScrapeApi({
      limit: scrapeForm.limit,
      platform: scrapeForm.platform || undefined,
    });
    notifyScrapeRunCreated({
      message: `任务 #${result.run.id} 已进入队列，范围：${formatPlatformLabel(result.platform)}，上限 ${result.limit} 条。`,
      runId: result.run.id,
      title: '批量抓取已创建',
    });
    await loadScrapeRuns();
  } catch (error) {
    console.error('Failed to trigger batch scrape:', error);
    ElMessage.error('投递批量抓取失败');
  } finally {
    scrapeSubmitting.value = false;
  }
}

async function submitTag() {
  if (!selectedProduct.value || !tagForm.tagCode) {
    ElMessage.warning('请选择一个标签');
    return;
  }

  tagSubmitting.value = true;
  try {
    const updatedTags = await addSkuProductTagApi(selectedProduct.value.id, {
      tagCode: tagForm.tagCode,
      tagValue: tagForm.tagValue || undefined,
    });
    selectedProduct.value.tags = updatedTags;
    tableData.value = tableData.value.map((item) =>
      item.id === selectedProduct.value?.id ? { ...item, tags: updatedTags } : item,
    );
    ElMessage.success('标签已添加');
    tagForm.tagCode = '';
    tagForm.tagValue = '';
  } catch (error) {
    console.error('Failed to add tag:', error);
    ElMessage.error('添加标签失败');
  } finally {
    tagSubmitting.value = false;
  }
}

async function removeTag(tag: SkuTag) {
  if (!selectedProduct.value) {
    return;
  }

  tagSubmitting.value = true;
  try {
    const updatedTags = await deleteSkuProductTagApi(selectedProduct.value.id, tag.id);
    selectedProduct.value.tags = updatedTags;
    tableData.value = tableData.value.map((item) =>
      item.id === selectedProduct.value?.id ? { ...item, tags: updatedTags } : item,
    );
    ElMessage.success('标签已删除');
  } catch (error) {
    console.error('Failed to remove tag:', error);
    ElMessage.error('删除标签失败');
  } finally {
    tagSubmitting.value = false;
  }
}

function handleSearch() {
  queryForm.page = 1;
  void loadProducts();
}

function handleReset() {
  queryFormRef.value?.resetFields();
  queryForm.keyword = '';
  queryForm.brandName = '';
  queryForm.platform = '';
  queryForm.tagCode = '';
  queryForm.status = 1;
  queryForm.page = 1;
  queryForm.pageSize = 10;
  void loadProducts();
}

function handlePageChange(page: number) {
  queryForm.page = page;
  void loadProducts();
}

function handlePageSizeChange(pageSize: number) {
  queryForm.page = 1;
  queryForm.pageSize = pageSize;
  void loadProducts();
}

function formatCategory(item: SkuProductListItem) {
  return [item.categoryLevel1, item.categoryLevel2, item.categoryLevel3]
    .filter(Boolean)
    .join(' / ');
}

function formatStatus(status: number) {
  if (status === 1) return '在售';
  if (status === 0) return '下架';
  return '删除';
}

function formatTaskName(taskName: string) {
  if (taskName === 'scrape_product') return '单商品抓取';
  if (taskName === 'scrape_active_products') return '批量抓取';
  return taskName;
}

function formatPlatformLabel(platform?: null | string) {
  const matched = platformOptions.find((item) => item.value === platform);
  return matched?.label ?? '全部平台';
}

function notifyScrapeRunCreated(options: { message: string; runId: number; title: string }) {
  ElNotification({
    duration: 6000,
    message: `${options.message} 点击此通知可打开任务详情。`,
    onClick: () => {
      void router.push({
        path: '/data-center/sku-repository',
        query: { runId: String(options.runId) },
      });
    },
    title: options.title,
    type: 'success',
  });
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

function taskLifecycleSteps(row: ScrapeTaskRun | null) {
  const status = row?.status ?? 'PENDING';
  const steps = [
    { key: 'PENDING', label: '排队中' },
    { key: 'RUNNING', label: '执行中' },
    { key: 'SUCCESS', label: '成功' },
    { key: 'PARTIAL_SUCCESS', label: '部分成功' },
    { key: 'FAILED', label: '失败' },
    { key: 'TIMEOUT', label: '超时' },
  ];
  return steps.map((step) => ({
    ...step,
    active: step.key === status,
  }));
}

function failureSummary(row: ScrapeTaskRun | null) {
  if (!row) return [];
  const summary = new Map<string, number>();
  for (const item of row.failedItems) {
    const reason = String(item.error || item.reason || '未知错误');
    summary.set(reason, (summary.get(reason) ?? 0) + 1);
  }
  return [...summary.entries()].map(([reason, count]) => ({ count, reason }));
}

function getStatusCount(status: string) {
  return scrapeOverview.value?.statusCounts[status] ?? 0;
}

function formatScheduleSummary() {
  const schedule = scrapeOverview.value?.schedule;
  if (!schedule) {
    return '调度配置加载中';
  }
  const parts = [
    `维护 ${schedule.maintenanceIntervalMinutes} 分钟/次`,
  ];
  if (schedule.periodicScrapeEnabled) {
    const platform = schedule.periodicScrapePlatform || '全部平台';
    parts.push(
      `采集 ${schedule.periodicScrapeIntervalMinutes} 分钟/次 · ${platform} · ${schedule.periodicScrapeLimit} 条`,
    );
  } else {
    parts.push('周期采集关闭');
  }
  if (schedule.categorySyncEnabled) {
    parts.push(`类目 ${schedule.categorySyncHours} 小时/次`);
  }
  return parts.join(' ｜ ');
}

function canInspectRun(row: ScrapeTaskRun | null) {
  return Boolean(
    row
    && (
      row.failureCount > 0
      || row.status === 'FAILED'
      || row.status === 'PARTIAL_SUCCESS'
      || row.status === 'TIMEOUT'
    ),
  );
}

onMounted(async () => {
  await Promise.all([loadTags(), loadProducts(), loadScrapeRuns()]);
  await openRunDetailFromRoute();
});

watch(
  () => route.query.runId,
  () => {
    void openRunDetailFromRoute();
  },
);

watch(
  () => route.query.taskStatus,
  () => {
    void loadScrapeRuns();
  },
);
</script>

<template>
  <div class="sku-repository-page p-5">
    <div class="hero-grid mb-5 grid gap-4 md:grid-cols-4">
      <div class="hero-card">
        <span class="hero-label">商品总量</span>
        <strong class="hero-value">{{ summary.totalCount }}</strong>
      </div>
      <div class="hero-card">
        <span class="hero-label">当前页商品</span>
        <strong class="hero-value">{{ summary.currentCount }}</strong>
      </div>
      <div class="hero-card">
        <span class="hero-label">当前页品牌数</span>
        <strong class="hero-value">{{ summary.uniqueBrands }}</strong>
      </div>
      <div class="hero-card">
        <span class="hero-label">自营标签命中</span>
        <strong class="hero-value">{{ summary.selfOperatedCount }}</strong>
      </div>
    </div>

    <div class="card-box mb-5 p-5">
      <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold">抓取任务</h2>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
            手动投递重抓任务，并查看最近一次执行结果。
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <ElSelect
            v-model="scrapeForm.platform"
            clearable
            placeholder="全部平台"
            style="width: 140px"
          >
            <ElOption
              v-for="item in platformOptions"
              :key="`scrape-${item.value}`"
              :label="item.label"
              :value="item.value"
            />
          </ElSelect>
          <ElInputNumber
            v-model="scrapeForm.limit"
            :max="200"
            :min="1"
            controls-position="right"
            style="width: 140px"
          />
          <ElButton :disabled="!canOperateTasks" :loading="scrapeSubmitting" type="primary" @click="triggerBatchScrape">
            立即批量抓取
          </ElButton>
          <ElButton @click="loadScrapeRuns">刷新任务</ElButton>
        </div>
      </div>

      <div class="mb-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div class="text-xs font-semibold text-slate-500">开放任务</div>
          <div class="mt-2 flex items-end gap-2">
            <span class="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {{ scrapeOverview?.openRunCount ?? 0 }}
            </span>
            <span class="pb-1 text-xs text-slate-500">
              排队 {{ getStatusCount('PENDING') }} / 执行 {{ getStatusCount('RUNNING') }}
            </span>
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div class="text-xs font-semibold text-slate-500">终态成功率</div>
          <div class="mt-2 flex items-end gap-2">
            <span class="text-2xl font-bold text-emerald-600">
              {{ scrapeOverview?.successRate ?? 0 }}%
            </span>
            <span class="pb-1 text-xs text-slate-500">
              共 {{ scrapeOverview?.totalRuns ?? 0 }} 次
            </span>
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div class="text-xs font-semibold text-slate-500">问题任务</div>
          <div class="mt-2 flex items-end gap-2">
            <span class="text-2xl font-bold text-rose-600">
              {{ getStatusCount('FAILED') + getStatusCount('PARTIAL_SUCCESS') + getStatusCount('TIMEOUT') }}
            </span>
            <span class="pb-1 text-xs text-slate-500">
              失败 {{ getStatusCount('FAILED') }} / 超时 {{ getStatusCount('TIMEOUT') }}
            </span>
          </div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
          <div class="text-xs font-semibold text-slate-500">最近成功</div>
          <div class="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
            {{ scrapeOverview?.latestSuccessRun?.finishedAt || scrapeOverview?.latestSuccessRun?.updatedAt || '-' }}
          </div>
          <div class="mt-1 truncate text-xs text-slate-500">
            {{ scrapeOverview?.latestSuccessRun?.summaryMessage || '暂无成功任务' }}
          </div>
        </div>
      </div>

      <div class="mb-4 flex flex-wrap items-center gap-2 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700 dark:border-blue-500/30 dark:bg-blue-500/10 dark:text-blue-300">
        <span class="font-semibold">调度配置</span>
        <span>{{ formatScheduleSummary() }}</span>
      </div>

      <div
        v-if="scrapeOverview?.latestProblemRun"
        class="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-rose-100 bg-rose-50 px-4 py-3 dark:border-rose-500/30 dark:bg-rose-500/10"
      >
        <div class="min-w-0">
          <div class="text-sm font-semibold text-rose-700 dark:text-rose-300">
            最近问题任务 #{{ scrapeOverview.latestProblemRun.id }}
            <ElTag class="ml-2" size="small" :type="formatRunStatus(scrapeOverview.latestProblemRun.status)">
              {{ formatRunStatusLabel(scrapeOverview.latestProblemRun.status) }}
            </ElTag>
          </div>
          <div class="mt-1 truncate text-xs text-rose-600 dark:text-rose-300">
            {{ scrapeOverview.latestProblemRun.summaryMessage || scrapeOverview.latestProblemRun.errorMessage || '-' }}
          </div>
        </div>
        <ElButton link type="danger" @click="openRunDetail(scrapeOverview.latestProblemRun.id)">
          查看详情
        </ElButton>
      </div>

      <ElTable v-loading="scrapeLoading" :data="scrapeRuns" border stripe>
        <ElTableColumn label="任务类型" min-width="120">
          <template #default="{ row }">
            {{ formatTaskName(row.taskName) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" min-width="120">
          <template #default="{ row }">
            <ElTag :type="formatRunStatus(row.status)">
              {{ formatRunStatusLabel(row.status) }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="平台" min-width="90" prop="platform" />
        <ElTableColumn label="执行概况" min-width="180">
          <template #default="{ row }">
            {{ row.successCount }}/{{ row.processedCount }} 成功
            <span v-if="row.failureCount">，失败 {{ row.failureCount }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="摘要" min-width="240">
          <template #default="{ row }">
            <div class="text-sm text-slate-600 dark:text-slate-300">
              {{ row.summaryMessage || '-' }}
            </div>
            <div v-if="row.errorMessage" class="mt-1 text-xs text-rose-500">
              {{ row.errorMessage }}
            </div>
          </template>
        </ElTableColumn>
        <ElTableColumn label="请求" min-width="220">
          <template #default="{ row }">
            <div v-if="row.requestedUrl" class="line-clamp-2 text-sm text-slate-500 dark:text-slate-400">
              {{ row.requestedUrl }}
            </div>
            <span v-else class="text-sm text-slate-500 dark:text-slate-400">
              批量 {{ row.requestedLimit || 0 }} 条
            </span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="创建时间" min-width="170" prop="createdAt" />
        <ElTableColumn label="结束时间" min-width="170" prop="finishedAt" />
        <ElTableColumn label="操作" min-width="120" fixed="right">
          <template #default="{ row }">
            <ElButton
              v-if="canInspectRun(row)"
              link
              type="primary"
              @click="openRunDetail(row.id)"
            >
              查看失败项
            </ElButton>
            <span v-else class="text-xs text-slate-400 dark:text-slate-500">-</span>
          </template>
        </ElTableColumn>
      </ElTable>

      <ElEmpty
        v-if="!scrapeLoading && scrapeRuns.length === 0"
        class="py-8"
        description="当前筛选下暂无抓取任务，可立即创建一批抓取任务验证链路"
        :image-size="72"
      >
        <ElButton :disabled="!canOperateTasks" :loading="scrapeSubmitting" type="primary" @click="triggerBatchScrape">
          立即批量抓取
        </ElButton>
      </ElEmpty>
    </div>

    <div class="card-box mb-5 p-5">
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold">SKU 资源库</h2>
          <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
            管理商品基本属性、规格参数和运营标签。
          </p>
        </div>
      </div>

      <ElForm ref="queryFormRef" :inline="true" :model="queryForm" class="sku-filter">
        <ElFormItem label="关键词" prop="keyword">
          <ElInput
            v-model="queryForm.keyword"
            clearable
            placeholder="搜索 SKU / 商品名称"
            style="width: 220px"
          />
        </ElFormItem>
        <ElFormItem label="品牌" prop="brandName">
          <ElInput
            v-model="queryForm.brandName"
            clearable
            placeholder="按品牌筛选"
            style="width: 180px"
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
        <ElFormItem label="标签" prop="tagCode">
          <ElSelect
            v-model="queryForm.tagCode"
            clearable
            filterable
            placeholder="全部标签"
            style="width: 180px"
          >
            <ElOption
              v-for="item in tags"
              :key="item.tagCode"
              :label="item.tagName"
              :value="item.tagCode"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="状态" prop="status">
          <ElSelect v-model="queryForm.status" placeholder="状态" style="width: 140px">
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

    <div class="card-box overflow-hidden p-5">
      <ElTable v-loading="loading" :data="tableData" border stripe>
        <ElTableColumn label="商品" min-width="340">
          <template #default="{ row }">
            <div class="product-cell">
              <img
                v-if="row.mainImageUrl"
                :src="row.mainImageUrl"
                alt="product"
                class="product-image"
              />
              <div class="min-w-0">
                <div class="truncate font-medium text-slate-900 dark:text-slate-100">
                  {{ row.normalizedName || row.productName }}
                </div>
                <div class="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  原始名：{{ row.productName }}
                </div>
                <div class="mt-1 text-xs text-slate-400 dark:text-slate-500">SKU：{{ row.skuId }}</div>
              </div>
            </div>
          </template>
        </ElTableColumn>
        <ElTableColumn label="品牌" min-width="110" prop="brandName" />
        <ElTableColumn label="平台" min-width="90" prop="platform" />
        <ElTableColumn label="店铺" min-width="180" prop="shopName" />
        <ElTableColumn label="三级分类" min-width="220">
          <template #default="{ row }">
            <span>{{ formatCategory(row) || '-' }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="标签" min-width="220">
          <template #default="{ row }">
            <div class="tag-list">
              <ElTag
                v-for="tag in row.tags"
                :key="`${row.id}-${tag.tagCode}`"
                class="mr-2 mb-2"
                effect="plain"
                round
                size="small"
              >
                {{ tag.tagName }}
              </ElTag>
              <span v-if="row.tags.length === 0" class="text-xs text-slate-400 dark:text-slate-500">暂无标签</span>
            </div>
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" min-width="100">
          <template #default="{ row }">
            <ElTag :type="row.status === 1 ? 'success' : row.status === 0 ? 'warning' : 'danger'">
              {{ formatStatus(row.status) }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="更新时间" min-width="170" prop="updatedAt" />
        <ElTableColumn fixed="right" label="操作" min-width="110">
          <template #default="{ row }">
            <ElButton link type="primary" @click="openDetail(row.id)">查看详情</ElButton>
          </template>
        </ElTableColumn>
      </ElTable>

      <ElEmpty
        v-if="!loading && tableData.length === 0"
        class="py-10"
        description="当前筛选条件下暂无 SKU 数据，可重置条件或先触发抓取补充商品库"
        :image-size="96"
      >
        <div class="flex justify-center gap-3">
          <ElButton @click="handleReset">重置筛选</ElButton>
          <ElButton
            :disabled="!canOperateTasks"
            :loading="scrapeSubmitting"
            type="primary"
            @click="triggerBatchScrape"
          >
            立即批量抓取
          </ElButton>
        </div>
      </ElEmpty>

      <div class="mt-4 flex justify-end">
        <ElPagination
          :current-page="queryForm.page"
          :page-size="queryForm.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          background
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </div>

    <ElDrawer v-model="drawerVisible" size="48%" title="SKU 详情">
      <ElSkeleton v-if="detailLoading" :rows="8" animated />
      <template v-else-if="selectedProduct">
        <div class="detail-section">
          <div class="detail-head">
            <img
              v-if="selectedProduct.mainImageUrl"
              :src="selectedProduct.mainImageUrl"
              alt="detail"
              class="detail-image"
            />
            <div class="min-w-0">
              <h3 class="text-lg font-semibold">
                {{ selectedProduct.normalizedName || selectedProduct.productName }}
              </h3>
              <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">{{ selectedProduct.productName }}</p>
            </div>
          </div>

          <ElDescriptions :column="2" border class="mt-5">
            <ElDescriptionsItem label="SKU">
              {{ selectedProduct.skuId }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="平台">
              {{ selectedProduct.platform }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="品牌">
              {{ selectedProduct.brandName || '-' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="店铺">
              {{ selectedProduct.shopName || '-' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="分类" :span="2">
              {{ formatCategory(selectedProduct) || '-' }}
            </ElDescriptionsItem>
            <ElDescriptionsItem label="商品链接" :span="2">
              <a
                v-if="selectedProduct.productUrl"
                :href="selectedProduct.productUrl"
                class="text-blue-500"
                rel="noreferrer"
                target="_blank"
              >
                {{ selectedProduct.productUrl }}
              </a>
              <span v-else>-</span>
            </ElDescriptionsItem>
          </ElDescriptions>

          <div class="mt-6">
            <div class="flex items-center justify-between gap-3">
              <div class="section-title">标签</div>
              <div class="flex items-center gap-2">
                <ElButton
                  v-if="selectedProduct.productUrl"
                  :disabled="!canOperateTasks"
                  :loading="singleScrapeSubmitting"
                  plain
                  size="small"
                  @click="triggerSelectedProductScrape"
                >
                  立即重抓
                </ElButton>
                <ElButton
                  :disabled="!canGovernData"
                  plain
                  size="small"
                  type="primary"
                  @click="openTagEditor"
                >
                  编辑标签
                </ElButton>
              </div>
            </div>
            <div class="mt-3 tag-list">
              <ElTag
                v-for="tag in selectedProduct.tags"
                :key="`${selectedProduct.id}-${tag.tagCode}`"
                class="mr-2 mb-2"
                :closable="true"
                round
                @close="canGovernData && removeTag(tag)"
              >
                {{ tag.tagName }}
                <span v-if="tag.tagValue"> · {{ tag.tagValue }}</span>
              </ElTag>
              <ElEmpty v-if="selectedProduct.tags.length === 0" description="暂无标签" :image-size="72" />
            </div>
          </div>

          <div class="mt-6">
            <div class="section-title">参数详情</div>
            <ElTable :data="selectedProduct.attributes" border class="mt-3">
              <ElTableColumn label="分组" min-width="120" prop="attrGroup" />
              <ElTableColumn label="参数名" min-width="160" prop="attrName" />
              <ElTableColumn label="参数值" min-width="180">
                <template #default="{ row }">
                  {{ row.attrValue }}{{ row.attrUnit || '' }}
                </template>
              </ElTableColumn>
            </ElTable>
          </div>
        </div>
      </template>
    </ElDrawer>

    <ElDialog v-model="editTagsVisible" title="编辑标签" width="420px">
      <ElForm label-position="top">
        <ElFormItem label="标签">
          <ElSelect
            v-model="tagForm.tagCode"
            clearable
            filterable
            placeholder="选择要添加的标签"
            style="width: 100%"
          >
            <ElOption
              v-for="item in tags"
              :key="item.tagCode"
              :label="item.tagName"
              :value="item.tagCode"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="标签附加值">
          <ElInput
            v-model="tagForm.tagValue"
            clearable
            placeholder="可选，如：直营、重点维护、直降500元"
          />
        </ElFormItem>
      </ElForm>

      <template #footer>
        <div class="flex justify-end gap-3">
          <ElButton @click="editTagsVisible = false">关闭</ElButton>
          <ElButton
            :disabled="!canGovernData"
            :loading="tagSubmitting"
            type="primary"
            @click="submitTag"
          >
            添加标签
          </ElButton>
        </div>
      </template>
    </ElDialog>

    <ElDialog v-model="runDetailVisible" title="抓取失败明细" width="760px">
      <div v-if="selectedRun" class="space-y-4">
        <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-300">
          <div><strong>任务类型：</strong>{{ formatTaskName(selectedRun.taskName) }}</div>
          <div class="mt-2"><strong>执行状态：</strong>{{ formatRunStatusLabel(selectedRun.status) }}</div>
          <div class="mt-2"><strong>任务摘要：</strong>{{ selectedRun.summaryMessage || '-' }}</div>
          <div class="mt-2"><strong>触发来源：</strong>{{ selectedRun.triggerSource }}</div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <div class="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">任务生命周期</div>
          <div class="grid gap-2 md:grid-cols-6">
            <div
              v-for="step in taskLifecycleSteps(selectedRun)"
              :key="step.key"
              class="rounded-xl border px-3 py-2 text-center text-xs font-semibold"
              :class="step.active ? 'border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-500/40 dark:bg-blue-500/10 dark:text-blue-300' : 'border-slate-200 bg-slate-50 text-slate-400 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-500'"
            >
              {{ step.label }}
            </div>
          </div>
          <div class="mt-3 grid gap-3 text-xs text-slate-500 md:grid-cols-3">
            <div>创建：{{ selectedRun.createdAt }}</div>
            <div>开始：{{ selectedRun.startedAt || '-' }}</div>
            <div>结束：{{ selectedRun.finishedAt || '-' }}</div>
          </div>
        </div>

        <div
          v-if="failureSummary(selectedRun).length"
          class="rounded-2xl border border-rose-100 bg-rose-50 p-4 dark:border-rose-500/30 dark:bg-rose-500/10"
        >
          <div class="mb-3 text-sm font-semibold text-rose-700 dark:text-rose-300">失败原因聚合</div>
          <div class="space-y-2">
            <div
              v-for="item in failureSummary(selectedRun)"
              :key="item.reason"
              class="flex items-center justify-between gap-3 rounded-lg bg-white px-3 py-2 text-sm dark:bg-slate-900"
            >
              <span class="text-rose-700 dark:text-rose-300">{{ item.reason }}</span>
              <ElTag type="danger">{{ item.count }} 次</ElTag>
            </div>
          </div>
        </div>

        <ElTable :data="selectedRun.failedItems" border max-height="360">
          <ElTableColumn label="商品ID" min-width="100" prop="product_id" />
          <ElTableColumn label="平台" min-width="90" prop="platform" />
          <ElTableColumn label="请求链接" min-width="240">
            <template #default="{ row }">
              <div class="line-clamp-2 text-sm text-slate-500">{{ row.url || '-' }}</div>
            </template>
          </ElTableColumn>
          <ElTableColumn label="错误信息" min-width="260">
            <template #default="{ row }">
              <div class="text-sm text-rose-500">{{ row.error || '-' }}</div>
            </template>
          </ElTableColumn>
        </ElTable>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <ElButton @click="runDetailVisible = false">关闭</ElButton>
          <ElButton
            v-if="canInspectRun(selectedRun)"
            :loading="retrySubmitting"
            :disabled="!canOperateTasks"
            type="primary"
            @click="retrySelectedRun"
          >
            重试任务
          </ElButton>
        </div>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.sku-repository-page {
  background:
    radial-gradient(circle at top left, rgb(249 239 219 / 90%), transparent 30%),
    linear-gradient(180deg, #f6f7fb 0%, #eef2f7 100%);
  min-height: 100%;
}

.dark .sku-repository-page {
  background:
    radial-gradient(circle at top left, rgb(59 130 246 / 16%), transparent 30%),
    linear-gradient(180deg, #020617 0%, #0f172a 100%);
}

.hero-card {
  border: 1px solid rgb(15 23 42 / 8%);
  border-radius: 20px;
  background: linear-gradient(135deg, rgb(255 255 255 / 95%), rgb(255 248 238 / 92%));
  box-shadow: 0 18px 45px rgb(15 23 42 / 8%);
  padding: 20px;
}

.dark .hero-card {
  border-color: rgb(51 65 85 / 80%);
  background: linear-gradient(135deg, rgb(15 23 42 / 96%), rgb(30 41 59 / 92%));
  box-shadow: 0 18px 45px rgb(0 0 0 / 24%);
}

.hero-label {
  color: #64748b;
  display: block;
  font-size: 13px;
  margin-bottom: 10px;
}

.dark .hero-label {
  color: #94a3b8;
}

.hero-value {
  color: #0f172a;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.dark .hero-value {
  color: #f8fafc;
}

.product-cell {
  align-items: center;
  display: flex;
  gap: 14px;
}

.product-image {
  border: 1px solid rgb(226 232 240);
  border-radius: 14px;
  height: 64px;
  object-fit: cover;
  width: 64px;
}

.dark .product-image {
  border-color: rgb(51 65 85);
}

.detail-head {
  align-items: center;
  display: flex;
  gap: 16px;
}

.detail-image {
  border: 1px solid rgb(226 232 240);
  border-radius: 18px;
  height: 88px;
  object-fit: cover;
  width: 88px;
}

.dark .detail-image {
  border-color: rgb(51 65 85);
}

.section-title {
  color: #0f172a;
  font-size: 15px;
  font-weight: 600;
}

.dark .section-title {
  color: #f8fafc;
}

.tag-list {
  align-items: flex-start;
  display: flex;
  flex-wrap: wrap;
}
</style>
