<script lang="ts" setup>
import type {
  CategoryNode,
  MappingRule,
  SkuComparison,
} from '#/api/sku-repository';

import { computed, onMounted, reactive, ref } from 'vue';

import { usePreferences } from '@vben/preferences';
import { useUserStore } from '@vben/stores';

import {
  ElButton,
  ElCol,
  ElDialog,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElMessage,
  ElOption,
  ElPagination,
  ElRow,
  ElSelect,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTree,
} from 'element-plus';

import {
  batchApplyMappingRulesApi,
  createMappingRuleApi,
  deleteMappingRuleApi,
  getCategoryTreeApi,
  getMappingRulesApi,
  getSkuComparisonsApi,
  getSkuProductsApi,
  importCategoryTreeApi,
  reviewSkuComparisonApi,
  syncJdCategoryTreeApi,
  triggerAutoMatchApi,
  toggleMappingRuleStatusApi,
  updateMappingRuleApi,
} from '#/api/sku-repository';

const activeTab = ref('category');
const loading = ref(false);
const { isDark } = usePreferences();
const userStore = useUserStore();
const canGovernData = computed(() =>
  userStore.userRoles.some((role) => ['admin', 'super'].includes(role)),
);
const canAdminConfigure = computed(() =>
  userStore.userRoles.some((role) => ['super'].includes(role)),
);

// --- Metrics ---
const summary = reactive({
  categoryCount: 0,
  ruleCount: 0,
  matchCount: 0,
  activeRuleCount: 0,
});

const metricCards = computed(() => [
  {
    accent: isDark.value ? 'from-blue-500/10 to-indigo-500/0' : 'from-blue-500/20 to-indigo-500/5',
    label: '类目总数 (JD)',
    value: summary.categoryCount,
  },
  {
    accent: isDark.value ? 'from-emerald-500/10 to-teal-500/0' : 'from-emerald-500/20 to-teal-500/5',
    label: '映射规则总数',
    value: summary.ruleCount,
  },
  {
    accent: isDark.value ? 'from-violet-500/10 to-purple-500/0' : 'from-violet-500/20 to-purple-500/5',
    label: '已激活规则',
    value: summary.activeRuleCount,
  },
  {
    accent: isDark.value ? 'from-orange-500/10 to-amber-500/0' : 'from-orange-500/20 to-amber-500/5',
    label: '同款匹配关系',
    value: summary.matchCount,
  },
]);

const comparisonStageCards = computed(() => {
  const pending = comparisons.value.filter((item) => item.status === 0).length;
  const confirmed = comparisons.value.filter((item) => item.status === 1).length;
  const rejected = comparisons.value.filter((item) => item.status < 0).length;
  const lowConfidence = comparisons.value.filter(
    (item) => item.status === 0 || (item.matchScore ?? 0) < 80,
  ).length;

  return [
    { label: '待匹配', value: Math.max(summary.categoryCount - summary.matchCount, 0), tone: 'info' as const },
    { label: '自动匹配结果', value: comparisonTotal.value, tone: 'primary' as const },
    { label: '低置信度待人工确认', value: lowConfidence || pending, tone: 'warning' as const },
    { label: '已确认映射', value: confirmed, tone: 'success' as const },
    { label: '已过滤', value: rejected, tone: 'info' as const },
  ];
});

// --- Category Tree ---
const categoryTree = ref<CategoryNode[]>([]);
const currentCategory = ref<CategoryNode | null>(null);
const categoryProducts = ref<any[]>([]);
const categoryImportVisible = ref(false);
const categoryImportSubmitting = ref(false);
const categorySyncSubmitting = ref(false);
const categoryImportText = ref('');
const treeProps = {
  label: 'name',
  children: 'children',
};

const categoryOptions = computed(() => {
  const result: Array<{ id: number; label: string }> = [];
  const walk = (nodes: CategoryNode[], parentLabels: string[] = []) => {
    nodes.forEach((node) => {
      const labels = [...parentLabels, node.name];
      result.push({
        id: node.id,
        label: labels.join(' / '),
      });
      if (node.children?.length) {
        walk(node.children, labels);
      }
    });
  };
  walk(categoryTree.value);
  return result;
});

async function loadCategoryTree() {
  loading.value = true;
  try {
    const data = await getCategoryTreeApi('jd');
    categoryTree.value = data;
    // Simple count of nodes (recursive)
    const countNodes = (nodes: CategoryNode[]): number => {
      return nodes.reduce((acc, node) => acc + 1 + (node.children ? countNodes(node.children) : 0), 0);
    };
    summary.categoryCount = countNodes(data);
  } catch (error) {
    console.error('Failed to load category tree:', error);
    ElMessage.error('加载类目树失败');
  } finally {
    loading.value = false;
  }
}

async function handleNodeClick(data: CategoryNode) {
  currentCategory.value = data;
  loading.value = true;
  try {
    const res = await getSkuProductsApi({
      page: 1,
      pageSize: 50,
      categoryId: data.id,
    } as any);
    categoryProducts.value = res.items;
  } catch {
    ElMessage.error('加载商品列表失败');
  } finally {
    loading.value = false;
  }
}

function openCategoryImportDialog() {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无类目体系配置权限');
    return;
  }
  categoryImportText.value = '';
  categoryImportVisible.value = true;
}

async function handleImportCategoryTree() {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无类目体系配置权限');
    return;
  }
  let parsed: any;
  try {
    parsed = JSON.parse(categoryImportText.value);
  } catch {
    ElMessage.error('JSON 格式不正确');
    return;
  }

  const nodes = Array.isArray(parsed) ? parsed : parsed.nodes;
  const platform = Array.isArray(parsed) ? 'jd' : parsed.platform || 'jd';
  if (!Array.isArray(nodes) || nodes.length === 0) {
    ElMessage.error('请提供非空的类目节点数组');
    return;
  }

  categoryImportSubmitting.value = true;
  try {
    const res = await importCategoryTreeApi({ nodes, platform });
    ElMessage.success(`已导入 ${res.importedCount} 个类目节点`);
    categoryImportVisible.value = false;
    currentCategory.value = null;
    categoryProducts.value = [];
    await loadCategoryTree();
  } catch {
    ElMessage.error('导入类目失败');
  } finally {
    categoryImportSubmitting.value = false;
  }
}

async function handleSyncJdCategoryTree() {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无类目体系配置权限');
    return;
  }
  categorySyncSubmitting.value = true;
  try {
    await syncJdCategoryTreeApi();
    ElMessage.success('京东类目同步任务已投递，稍后刷新体系查看结果');
  } catch {
    ElMessage.error('投递京东类目同步任务失败');
  } finally {
    categorySyncSubmitting.value = false;
  }
}

// --- Mapping Rules ---
const mappingRules = ref<MappingRule[]>([]);
const mappingTotal = ref(0);
const mappingQuery = reactive({
  keyword: '',
  page: 1,
  pageSize: 10,
  platform: '',
});

async function loadMappingRules() {
  loading.value = true;
  try {
    const res = await getMappingRulesApi(mappingQuery);
    mappingRules.value = res.items;
    mappingTotal.value = res.total;
    summary.ruleCount = res.total;
    summary.activeRuleCount = res.activeTotal;
  } catch {
    ElMessage.error('加载映射规则失败');
  } finally {
    loading.value = false;
  }
}

const dialogVisible = ref(false);
const editingRuleId = ref<number | null>(null);
const ruleForm = reactive({
  categoryId: undefined as number | undefined,
  platform: '',
  pattern: '',
  ruleType: 'KEYWORD',
  unifiedLabel: '',
  priority: 0,
  isActive: 1,
});

function resetRuleForm() {
  editingRuleId.value = null;
  ruleForm.categoryId = undefined;
  ruleForm.platform = '';
  ruleForm.pattern = '';
  ruleForm.ruleType = 'KEYWORD';
  ruleForm.unifiedLabel = '';
  ruleForm.priority = 0;
  ruleForm.isActive = 1;
}

function openCreateRuleDialog() {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无映射规则配置权限');
    return;
  }
  resetRuleForm();
  dialogVisible.value = true;
}

function openEditRuleDialog(rule: MappingRule) {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无映射规则配置权限');
    return;
  }
  editingRuleId.value = rule.id;
  ruleForm.categoryId = rule.categoryId ?? undefined;
  ruleForm.platform = rule.platform ?? '';
  ruleForm.pattern = rule.pattern;
  ruleForm.ruleType = rule.ruleType;
  ruleForm.unifiedLabel = rule.unifiedLabel;
  ruleForm.priority = rule.priority;
  ruleForm.isActive = rule.isActive;
  dialogVisible.value = true;
}

async function handleSubmitRule() {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无映射规则配置权限');
    return;
  }
  try {
    if (editingRuleId.value) {
      await updateMappingRuleApi(editingRuleId.value, ruleForm);
      ElMessage.success('规则已更新');
    } else {
      await createMappingRuleApi(ruleForm);
      ElMessage.success('规则已创建');
    }
    dialogVisible.value = false;
    resetRuleForm();
    await loadMappingRules();
  } catch {
    ElMessage.error(editingRuleId.value ? '更新失败' : '添加失败');
  }
}

async function handleToggleRule(row: MappingRule) {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无映射规则配置权限');
    return;
  }
  try {
    await toggleMappingRuleStatusApi(row.id, row.isActive === 1 ? 0 : 1);
    ElMessage.success('规则状态已更新');
    await loadMappingRules();
  } catch {
    ElMessage.error('更新状态失败');
  }
}

async function handleDeleteRule(row: MappingRule) {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无映射规则配置权限');
    return;
  }
  try {
    await deleteMappingRuleApi(row.id);
    ElMessage.success('规则已删除');
    await loadMappingRules();
  } catch {
    ElMessage.error('删除失败');
  }
}

async function handleBatchApply() {
  if (!canAdminConfigure.value) {
    ElMessage.warning('当前角色无映射规则配置权限');
    return;
  }
  loading.value = true;
  try {
    const res = await batchApplyMappingRulesApi();
    ElMessage.success(`已应用规则，更新 ${res.updatedCount} 个商品`);
    await loadMappingRules();
    if (currentCategory.value) {
      await handleNodeClick(currentCategory.value);
    }
  } catch {
    ElMessage.error('应用失败');
  } finally {
    loading.value = false;
  }
}

// --- Competition Comparison ---
const comparisons = ref<SkuComparison[]>([]);
const comparisonTotal = ref(0);
const comparisonQuery = reactive({
  page: 1,
  pageSize: 10,
});

async function loadComparisons() {
  loading.value = true;
  try {
    const res = await getSkuComparisonsApi(comparisonQuery);
    comparisons.value = res.items;
    comparisonTotal.value = res.total;
    summary.matchCount = res.total;
  } catch {
    ElMessage.error('加载对比列表失败');
  } finally {
    loading.value = false;
  }
}

async function handleAutoMatch() {
  if (!canGovernData.value) {
    ElMessage.warning('当前角色无同款自动匹配权限');
    return;
  }
  loading.value = true;
  try {
    const res = await triggerAutoMatchApi();
    ElMessage.success(`自动匹配完成，新增 ${res.matchedCount} 组同款`);
    await loadComparisons();
  } catch {
    ElMessage.error('自动匹配失败');
  } finally {
    loading.value = false;
  }
}

function getComparisonStatusMeta(status: number) {
  if (status === 1) {
    return { label: '高置信', type: 'success' as const };
  }
  if (status === 0) {
    return { label: '待人工确认', type: 'warning' as const };
  }
  return { label: '已过滤', type: 'info' as const };
}

async function handleReviewComparison(comparisonId: number, approved: boolean) {
  if (!canGovernData.value) {
    ElMessage.warning('当前角色无同款映射确认权限');
    return;
  }
  loading.value = true;
  try {
    await reviewSkuComparisonApi(comparisonId, approved);
    ElMessage.success(approved ? '已确认匹配' : '已驳回该匹配');
    await loadComparisons();
  } catch {
    ElMessage.error(approved ? '确认匹配失败' : '驳回匹配失败');
  } finally {
    loading.value = false;
  }
}

// --- Lifecycle ---
onMounted(() => {
  loadCategoryTree();
  loadMappingRules();
  loadComparisons();
});

function handleTabChange(tab: any) {
  if (tab === 'category') loadCategoryTree();
  if (tab === 'mapping') loadMappingRules();
  if (tab === 'comparison') loadComparisons();
}
</script>

<template>
  <div class="mapping-center-page p-6">
    <!-- Header Hero -->
    <div class="mb-8 flex items-end justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">目录与映射中心</h1>
        <p class="mt-2 text-base text-slate-500 dark:text-slate-400">
          管理跨平台类目映射、商品名称归一化规则，以及基于 AI 的同款竞品自动匹配。
        </p>
      </div>
      <div class="flex items-center gap-3">
        <div class="platform-badge dark:bg-slate-800 dark:border-slate-700">
          <span class="text-xs uppercase tracking-widest text-slate-400">Core Platform</span>
          <strong class="text-sm font-bold text-slate-700 dark:text-slate-200">JD.COM</strong>
        </div>
      </div>
    </div>

    <!-- Metrics Grid -->
    <div class="mb-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
      <div
        v-for="item in metricCards"
        :key="item.label"
        class="metric-card relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
      >
        <div class="metric-card__glow absolute inset-0 bg-gradient-to-br opacity-60 dark:opacity-20" :class="item.accent"></div>
        <div class="relative z-10">
          <div class="text-sm font-medium text-slate-500 dark:text-slate-400">{{ item.label }}</div>
          <div class="mt-3 text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {{ item.value }}
          </div>
        </div>
      </div>
    </div>

    <ElTabs v-model="activeTab" class="custom-tabs" @tab-change="handleTabChange">
      <!-- Category Tab -->
      <ElTabPane label="类目体系管理" name="category">
        <ElRow :gutter="24">
          <ElCol :span="8">
            <div class="card-box h-full min-h-[600px] overflow-hidden dark:bg-slate-900 dark:border-slate-800">
              <div class="card-header border-b border-slate-100 p-5 dark:border-slate-800">
                <div class="flex items-center justify-between">
                  <span class="text-base font-bold text-slate-800 dark:text-slate-200">京东分类树</span>
                  <div class="flex items-center gap-2">
                    <ElButton
                      :loading="categorySyncSubmitting"
                      :disabled="!canAdminConfigure"
                      link
                      type="primary"
                      @click="handleSyncJdCategoryTree"
                    >
                      同步京东类目
                    </ElButton>
                    <ElButton link type="primary" :disabled="!canAdminConfigure" @click="openCategoryImportDialog">导入类目 JSON</ElButton>
                    <ElButton link type="primary" @click="loadCategoryTree">刷新体系</ElButton>
                  </div>
                </div>
              </div>
              <div class="p-2">
                <ElTree
                  v-loading="loading"
                  :data="categoryTree"
                  :props="treeProps"
                  highlight-current
                  default-expand-all
                  class="custom-tree dark:bg-transparent"
                  @node-click="handleNodeClick"
                >
                  <template #default="{ node, data }">
                    <span class="custom-tree-node">
                      <span class="node-label dark:text-slate-300">{{ node.label }}</span>
                      <ElTag v-if="data.level === 3" size="small" type="info" effect="plain" class="ml-2 rounded-md dark:bg-slate-800 dark:border-slate-700">L3</ElTag>
                    </span>
                  </template>
                </ElTree>
              </div>
            </div>
          </ElCol>
          <ElCol :span="16">
            <div v-if="!currentCategory" class="empty-state-card flex h-full flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-200 bg-slate-50/50 p-20 dark:border-slate-800 dark:bg-slate-900/40">
              <ElEmpty description="请从左侧选择一个类目以管理商品映射" />
            </div>
            <div v-else class="card-box min-h-[600px] dark:bg-slate-900 dark:border-slate-800">
              <div class="card-header flex items-center justify-between border-b border-slate-100 p-5 dark:border-slate-800">
                <div class="flex items-center gap-3">
                  <div class="h-10 w-1 bg-blue-500 rounded-full"></div>
                  <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">
                    {{ currentCategory.name }}
                    <span class="ml-2 text-sm font-normal text-slate-400">当前类目共 {{ categoryProducts.length }} 个商品</span>
                  </h3>
                </div>
              </div>
              <div class="p-5">
                <ElTable :data="categoryProducts" border stripe height="520" class="premium-table">
                  <ElTableColumn label="预览" width="80" align="center">
                    <template #default="{ row }">
                      <img :src="row.mainImageUrl" class="h-12 w-12 rounded-xl border border-slate-100 object-cover shadow-sm dark:border-slate-700" />
                    </template>
                  </ElTableColumn>
                  <ElTableColumn label="原始商品名称" prop="productName" show-overflow-tooltip min-width="200" />
                  <ElTableColumn label="归一化结果" show-overflow-tooltip min-width="200">
                    <template #default="{ row }">
                      <div class="flex items-center gap-2">
                        <span :class="row.normalizedName !== row.productName ? 'text-emerald-600 font-bold dark:text-emerald-400' : 'text-slate-400 italic'">
                          {{ row.normalizedName }}
                        </span>
                        <ElTag v-if="row.normalizedName !== row.productName" size="small" type="success" effect="plain" round>已转换</ElTag>
                      </div>
                    </template>
                  </ElTableColumn>
                  <ElTableColumn label="操作" width="100" align="center">
                    <template #default>
                      <ElButton link type="primary" class="font-bold">详情</ElButton>
                    </template>
                  </ElTableColumn>
                </ElTable>
              </div>
            </div>
          </ElCol>
        </ElRow>
      </ElTabPane>

      <!-- Mapping Rules Tab -->
      <ElTabPane label="归一化规则配置" name="mapping">
        <div class="card-box dark:bg-slate-900 dark:border-slate-800">
          <div class="flex items-center justify-between border-b border-slate-100 p-6 dark:border-slate-800">
            <div class="flex gap-4">
              <ElInput
                v-model="mappingQuery.keyword"
                placeholder="搜索规则关键词或标签..."
                class="premium-input w-80"
                clearable
                @keyup.enter="loadMappingRules"
              />
              <ElSelect
                v-model="mappingQuery.platform"
                clearable
                placeholder="全部平台"
                style="width: 140px"
              >
                <ElOption label="京东" value="jd" />
                <ElOption label="天猫" value="tmall" />
                <ElOption label="拼多多" value="pdd" />
              </ElSelect>
              <ElButton type="primary" class="premium-button" @click="loadMappingRules">执行查询</ElButton>
              <ElButton type="success" plain class="premium-button" :disabled="!canAdminConfigure" @click="handleBatchApply">立即批量应用规则</ElButton>
            </div>
            <ElButton type="primary" class="premium-button" :disabled="!canAdminConfigure" @click="openCreateRuleDialog">新增映射规则</ElButton>
          </div>

          <div class="p-6">
            <ElTable v-loading="loading" :data="mappingRules" border stripe class="premium-table">
              <ElTableColumn label="规则类型" width="110" align="center">
                <template #default="{ row }">
                  <ElTag effect="plain" :type="row.ruleType === 'REGEX' ? 'warning' : 'info'">
                    {{ row.ruleType }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn label="匹配模式 (Regex/Keyword)" prop="pattern" min-width="240" />
              <ElTableColumn label="映射目标标签" min-width="180">
                <template #default="{ row }">
                  <ElTag type="success" effect="dark" class="px-4 py-1 rounded-lg font-bold">{{ row.unifiedLabel }}</ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn label="平台 / 类目约束" min-width="220">
                <template #default="{ row }">
                  <div class="text-sm text-slate-600 dark:text-slate-300">
                    <div>{{ row.platform || '全平台' }}</div>
                    <div class="mt-1 text-xs text-slate-400">
                      {{ row.categoryId ? `类目 ID ${row.categoryId}` : '不限类目' }}
                    </div>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="执行优先级" width="120" align="center">
                <template #default="{ row }">
                  <span class="font-mono font-bold text-slate-600 dark:text-slate-400">{{ row.priority }}</span>
                </template>
              </ElTableColumn>
              <ElTableColumn label="当前状态" width="120" align="center">
                <template #default="{ row }">
                  <ElSwitch
                    :model-value="row.isActive === 1"
                    :disabled="!canAdminConfigure"
                    @change="handleToggleRule(row)"
                  />
                </template>
              </ElTableColumn>
              <ElTableColumn label="最近更新" prop="updatedAt" width="180" align="center" />
              <ElTableColumn label="管理" width="160" fixed="right" align="center">
                <template #default="{ row }">
                  <ElButton link type="primary" class="font-bold" :disabled="!canAdminConfigure" @click="openEditRuleDialog(row)">编辑</ElButton>
                  <ElButton link type="danger" class="font-bold" :disabled="!canAdminConfigure" @click="handleDeleteRule(row)">移除</ElButton>
                </template>
              </ElTableColumn>
            </ElTable>

            <div class="mt-6 flex justify-end">
              <ElPagination
                v-model:current-page="mappingQuery.page"
                :page-size="mappingQuery.pageSize"
                :total="mappingTotal"
                background
                layout="total, prev, pager, next, jumper"
                @current-change="loadMappingRules"
              />
            </div>
          </div>
        </div>
      </ElTabPane>

      <!-- Comparison Tab -->
      <ElTabPane label="同款商品对照表" name="comparison">
        <div class="card-box dark:bg-slate-900 dark:border-slate-800">
          <div class="flex items-center justify-between border-b border-slate-100 p-6 dark:border-slate-800">
            <div>
              <h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">跨平台同款映射库</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">已通过语义识别和视觉算法匹配的对照关系。</p>
            </div>
            <ElButton type="primary" class="premium-button shadow-blue-100" :disabled="!canGovernData" @click="handleAutoMatch">
              启动 AI 深度匹配引擎
            </ElButton>
          </div>

          <div class="p-6">
            <div class="mb-6 grid gap-4 md:grid-cols-5">
              <div
                v-for="item in comparisonStageCards"
                :key="item.label"
                class="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950"
              >
                <div class="text-xs font-semibold text-slate-500">{{ item.label }}</div>
                <div class="mt-2 flex items-end justify-between gap-2">
                  <strong class="text-2xl text-slate-900 dark:text-slate-100">{{ item.value }}</strong>
                  <ElTag :type="item.tone" size="small">流程</ElTag>
                </div>
              </div>
            </div>

            <ElTable v-loading="loading" :data="comparisons" border stripe class="premium-table">
              <ElTableColumn label="基准商品 (JD.COM)" min-width="320">
                <template #default="{ row }">
                  <div v-if="row.masterSku" class="flex items-center gap-4">
                    <img :src="row.masterSku.mainImageUrl" class="h-14 w-14 rounded-xl border border-slate-100 shadow-sm dark:border-slate-700" />
                    <div class="min-w-0">
                      <div class="truncate font-bold text-slate-900 dark:text-slate-100">{{ row.masterSku.productName }}</div>
                      <div class="mt-1 text-xs text-slate-400">SKU: {{ row.masterSku.skuId }}</div>
                    </div>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="竞端匹配商品" min-width="320">
                <template #default="{ row }">
                  <div v-if="row.linkedSku" class="flex items-center gap-4">
                    <div class="flex flex-col items-center gap-1">
                      <ElTag size="small" :type="row.linkedSku.platform === 'tmall' ? 'danger' : 'warning'" effect="dark" class="px-2">
                        {{ row.linkedSku.platform.toUpperCase() }}
                      </ElTag>
                      <img :src="row.linkedSku.mainImageUrl" class="h-14 w-14 rounded-xl border border-slate-100 shadow-sm dark:border-slate-700" />
                    </div>
                    <div class="min-w-0">
                      <div class="truncate font-bold text-slate-900 dark:text-slate-100">{{ row.linkedSku.productName }}</div>
                      <div class="mt-1 text-xs text-slate-400">SKU: {{ row.linkedSku.skuId }}</div>
                    </div>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="置信度" width="160" align="center">
                <template #default="{ row }">
                  <div class="flex flex-col items-center gap-1">
                    <div class="h-2 w-full max-w-[100px] overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                      <div
                        class="h-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all duration-1000"
                        :style="{ width: `${row.matchScore}%` }"
                      ></div>
                    </div>
                    <span class="font-mono text-sm font-bold text-blue-600 dark:text-blue-400">{{ row.matchScore }}% Match</span>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="匹配权重" width="140" align="center">
                <template #default="{ row }">
                  <ElTag :type="row.matchType === 'MANUAL' ? 'info' : 'success'" round effect="plain" class="dark:bg-slate-800 dark:border-slate-700">
                    {{ row.matchType === 'MANUAL' ? '人工校验' : 'AI 算法引擎' }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn label="分层状态" width="140" align="center">
                <template #default="{ row }">
                  <ElTag
                    :type="getComparisonStatusMeta(row.status).type"
                    round
                    effect="dark"
                  >
                    {{ getComparisonStatusMeta(row.status).label }}
                  </ElTag>
                </template>
              </ElTableColumn>
              <ElTableColumn label="命中依据" min-width="260">
                <template #default="{ row }">
                  <div class="flex flex-wrap gap-2">
                    <ElTag
                      v-for="reason in row.matchReasons"
                      :key="`${row.id}-${reason}`"
                      effect="plain"
                      size="small"
                      type="info"
                    >
                      {{ reason }}
                    </ElTag>
                  </div>
                </template>
              </ElTableColumn>
              <ElTableColumn label="人工处理" width="180" align="center">
                <template #default="{ row }">
                  <div v-if="row.status === 0" class="flex items-center justify-center gap-2">
                    <ElButton
                      link
                      type="success"
                      class="font-bold"
                      :disabled="!canGovernData"
                      @click="handleReviewComparison(row.id, true)"
                    >
                      确认匹配
                    </ElButton>
                    <ElButton
                      link
                      type="danger"
                      class="font-bold"
                      :disabled="!canGovernData"
                      @click="handleReviewComparison(row.id, false)"
                    >
                      驳回
                    </ElButton>
                  </div>
                  <span v-else class="text-xs text-slate-400">无需处理</span>
                </template>
              </ElTableColumn>
            </ElTable>

            <ElEmpty
              v-if="!loading && comparisons.length === 0"
              class="py-10"
              description="暂无同款映射结果，可先启动自动匹配生成候选关系"
              :image-size="90"
            >
              <ElButton type="primary" :disabled="!canGovernData" @click="handleAutoMatch">启动 AI 深度匹配引擎</ElButton>
            </ElEmpty>

            <div class="mt-6 flex justify-end">
              <ElPagination
                v-model:current-page="comparisonQuery.page"
                :page-size="comparisonQuery.pageSize"
                :total="comparisonTotal"
                background
                layout="total, prev, pager, next"
                @current-change="loadComparisons"
              />
            </div>
          </div>
        </div>
      </ElTabPane>
    </ElTabs>

    <!-- Add Rule Dialog -->
    <ElDialog
      v-model="dialogVisible"
      :title="editingRuleId ? '编辑映射规则' : '新增映射规则'"
      width="550px"
      class="premium-dialog"
    >
      <ElForm :model="ruleForm" label-position="top" class="p-4">
        <div class="grid grid-cols-2 gap-4">
          <ElFormItem label="规则类型">
            <ElSelect v-model="ruleForm.ruleType" style="width: 100%">
              <ElOption label="关键词" value="KEYWORD" />
              <ElOption label="正则" value="REGEX" />
            </ElSelect>
          </ElFormItem>
          <ElFormItem label="适用平台">
            <ElSelect v-model="ruleForm.platform" clearable placeholder="全平台" style="width: 100%">
              <ElOption label="京东" value="jd" />
              <ElOption label="天猫" value="tmall" />
              <ElOption label="拼多多" value="pdd" />
            </ElSelect>
          </ElFormItem>
        </div>
        <ElFormItem label="匹配模式 (Regex / Keyword)">
          <ElInput v-model="ruleForm.pattern" placeholder="例如: iPhone 15 Pro Max" />
        </ElFormItem>
        <ElFormItem label="归一化目标标签">
          <ElInput v-model="ruleForm.unifiedLabel" placeholder="例如: iPhone 15 PM" />
        </ElFormItem>
        <ElFormItem label="类目约束">
          <ElSelect
            v-model="ruleForm.categoryId"
            clearable
            filterable
            placeholder="不限类目"
            style="width: 100%"
          >
            <ElOption
              v-for="item in categoryOptions"
              :key="item.id"
              :label="item.label"
              :value="item.id"
            />
          </ElSelect>
        </ElFormItem>
        <div class="flex gap-10">
          <ElFormItem label="执行优先级" class="flex-1">
            <ElInputNumber v-model="ruleForm.priority" :min="0" :max="100" class="w-full" />
          </ElFormItem>
          <ElFormItem label="立即启用" class="w-32">
            <ElSwitch v-model="ruleForm.isActive" :active-value="1" :inactive-value="0" />
          </ElFormItem>
        </div>
      </ElForm>
      <template #footer>
        <div class="flex justify-end gap-3 p-4">
          <ElButton @click="dialogVisible = false">取消返回</ElButton>
          <ElButton type="primary" class="premium-button px-8" :disabled="!canAdminConfigure" @click="handleSubmitRule">
            {{ editingRuleId ? '保存修改' : '创建规则' }}
          </ElButton>
        </div>
      </template>
    </ElDialog>

    <ElDialog
      v-model="categoryImportVisible"
      title="导入京东类目树"
      width="720px"
      class="premium-dialog"
    >
      <div class="p-4">
        <ElInput
          v-model="categoryImportText"
          :rows="16"
          placeholder='粘贴 allSort 解析后的 JSON，例如 [{"name":"手机通讯","children":[{"name":"手机","children":[{"name":"智能手机","external_id":"653"}]}]}]'
          type="textarea"
        />
      </div>
      <template #footer>
        <div class="flex justify-end gap-3 p-4">
          <ElButton @click="categoryImportVisible = false">取消</ElButton>
          <ElButton
            :loading="categoryImportSubmitting"
            :disabled="!canAdminConfigure"
            class="premium-button px-8"
            type="primary"
            @click="handleImportCategoryTree"
          >
            导入并刷新
          </ElButton>
        </div>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.mapping-center-page {
  background:
    radial-gradient(circle at top left, var(--gradient-color-1, rgb(243 244 246 / 90%)), transparent 30%),
    radial-gradient(circle at bottom right, var(--gradient-color-2, rgb(219 234 254 / 50%)), transparent 30%),
    var(--page-bg, #f8fafc);
  min-height: 100%;
}

.dark .mapping-center-page {
  --gradient-color-1: rgb(15 23 42 / 90%);
  --gradient-color-2: rgb(30 41 59 / 50%);
  --page-bg: #020617;
}

.platform-badge {
  background: white;
  border: 1px solid #e2e8f0;
  padding: 8px 16px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 5%);
}

.dark .platform-badge {
  background: #1e293b;
  border-color: #334155;
}

.metric-card__glow {
  transition: opacity 0.3s ease;
}

.metric-card:hover .metric-card__glow {
  opacity: 0.8;
}

.card-box {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
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
  padding: 10px 24px;
  border-radius: 20px;
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
  font-weight: 600;
  color: #64748b;
  height: 48px;
  line-height: 48px;
}

.dark .custom-tabs :deep(.el-tabs__item) {
  color: #94a3b8;
}

.custom-tabs :deep(.el-tabs__item.is-active) {
  color: #1e293b;
}

.dark .custom-tabs :deep(.el-tabs__item.is-active) {
  color: #f1f5f9;
}

.custom-tree :deep(.el-tree-node__content) {
  height: 40px;
  border-radius: 8px;
  margin: 2px 8px;
}

.custom-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}

.dark .custom-tree :deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: #1e293b;
  color: #60a5fa;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.premium-table :deep(.el-table__header th) {
  background-color: #f8fafc;
  color: #475569;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: 0.025em;
  padding: 12px 0;
}
</style>
