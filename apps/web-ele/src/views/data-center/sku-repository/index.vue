<script lang="ts" setup>
import {
  ElButton,
  ElDescriptions,
  ElDescriptionsItem,
  ElDrawer,
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
import type { FormInstance } from 'element-plus';
import type {
  SkuProductDetail,
  SkuProductListItem,
  SkuTag,
} from '#/api';

import { computed, onMounted, reactive, ref } from 'vue';

import {
  getSkuProductDetailApi,
  getSkuProductsApi,
  getSkuTagsApi,
} from '#/api';

const loading = ref(false);
const detailLoading = ref(false);
const drawerVisible = ref(false);
const tableData = ref<SkuProductListItem[]>([]);
const total = ref(0);
const tags = ref<SkuTag[]>([]);
const selectedProduct = ref<null | SkuProductDetail>(null);

const queryFormRef = ref<FormInstance>();
interface QueryFormState {
  brandName: string;
  keyword: string;
  page: number;
  pageSize: number;
  platform: string;
  status: '' | -1 | 0 | 1;
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
  } finally {
    loading.value = false;
  }
}

async function loadTags() {
  tags.value = await getSkuTagsApi();
}

async function openDetail(productId: number) {
  drawerVisible.value = true;
  detailLoading.value = true;
  selectedProduct.value = null;
  try {
    selectedProduct.value = await getSkuProductDetailApi(productId);
  } finally {
    detailLoading.value = false;
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

onMounted(async () => {
  await Promise.all([loadTags(), loadProducts()]);
});
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
      <div class="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-bold">SKU 资源库</h2>
          <p class="mt-1 text-sm text-gray-500">
            管理商品基本属性、规格参数和运营标签。
          </p>
        </div>
      </div>

      <el-form ref="queryFormRef" :inline="true" :model="queryForm" class="sku-filter">
        <el-form-item label="关键词" prop="keyword">
          <el-input
            v-model="queryForm.keyword"
            clearable
            placeholder="搜索 SKU / 商品名称"
            style="width: 220px"
          />
        </el-form-item>
        <el-form-item label="品牌" prop="brandName">
          <el-input
            v-model="queryForm.brandName"
            clearable
            placeholder="按品牌筛选"
            style="width: 180px"
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
        <el-form-item label="标签" prop="tagCode">
          <el-select
            v-model="queryForm.tagCode"
            clearable
            filterable
            placeholder="全部标签"
            style="width: 180px"
          >
            <el-option
              v-for="item in tags"
              :key="item.tagCode"
              :label="item.tagName"
              :value="item.tagCode"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="queryForm.status" placeholder="状态" style="width: 140px">
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

    <div class="card-box overflow-hidden p-5">
      <el-table v-loading="loading" :data="tableData" border stripe>
        <el-table-column label="商品" min-width="340">
          <template #default="{ row }">
            <div class="product-cell">
              <img
                v-if="row.mainImageUrl"
                :src="row.mainImageUrl"
                alt="product"
                class="product-image"
              />
              <div class="min-w-0">
                <div class="truncate font-medium text-gray-900">
                  {{ row.normalizedName || row.productName }}
                </div>
                <div class="mt-1 text-xs text-gray-500">
                  原始名：{{ row.productName }}
                </div>
                <div class="mt-1 text-xs text-gray-400">SKU：{{ row.skuId }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="品牌" min-width="110" prop="brandName" />
        <el-table-column label="平台" min-width="90" prop="platform" />
        <el-table-column label="店铺" min-width="180" prop="shopName" />
        <el-table-column label="三级分类" min-width="220">
          <template #default="{ row }">
            <span>{{ formatCategory(row) || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="220">
          <template #default="{ row }">
            <div class="tag-list">
              <el-tag
                v-for="tag in row.tags"
                :key="`${row.id}-${tag.tagCode}`"
                class="mr-2 mb-2"
                effect="plain"
                round
                size="small"
              >
                {{ tag.tagName }}
              </el-tag>
              <span v-if="row.tags.length === 0" class="text-xs text-gray-400">暂无标签</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : row.status === 0 ? 'warning' : 'danger'">
              {{ formatStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="170" prop="updatedAt" />
        <el-table-column fixed="right" label="操作" min-width="110">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && tableData.length === 0"
        class="py-10"
        description="当前筛选条件下暂无 SKU 数据"
        :image-size="96"
      />

      <div class="mt-4 flex justify-end">
        <el-pagination
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

    <el-drawer v-model="drawerVisible" size="48%" title="SKU 详情">
      <el-skeleton v-if="detailLoading" :rows="8" animated />
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
              <p class="mt-2 text-sm text-gray-500">{{ selectedProduct.productName }}</p>
            </div>
          </div>

          <el-descriptions :column="2" border class="mt-5">
            <el-descriptions-item label="SKU">
              {{ selectedProduct.skuId }}
            </el-descriptions-item>
            <el-descriptions-item label="平台">
              {{ selectedProduct.platform }}
            </el-descriptions-item>
            <el-descriptions-item label="品牌">
              {{ selectedProduct.brandName || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="店铺">
              {{ selectedProduct.shopName || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="分类" :span="2">
              {{ formatCategory(selectedProduct) || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="商品链接" :span="2">
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
            </el-descriptions-item>
          </el-descriptions>

          <div class="mt-6">
            <div class="section-title">标签</div>
            <div class="mt-3 tag-list">
              <el-tag
                v-for="tag in selectedProduct.tags"
                :key="`${selectedProduct.id}-${tag.tagCode}`"
                class="mr-2 mb-2"
                round
              >
                {{ tag.tagName }}
                <span v-if="tag.tagValue"> · {{ tag.tagValue }}</span>
              </el-tag>
              <el-empty v-if="selectedProduct.tags.length === 0" description="暂无标签" :image-size="72" />
            </div>
          </div>

          <div class="mt-6">
            <div class="section-title">参数详情</div>
            <el-table :data="selectedProduct.attributes" border class="mt-3">
              <el-table-column label="分组" min-width="120" prop="attrGroup" />
              <el-table-column label="参数名" min-width="160" prop="attrName" />
              <el-table-column label="参数值" min-width="180">
                <template #default="{ row }">
                  {{ row.attrValue }}{{ row.attrUnit || '' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.sku-repository-page {
  background:
    radial-gradient(circle at top left, rgb(249 239 219 / 90%), transparent 30%),
    linear-gradient(180deg, #f6f7fb 0%, #eef2f7 100%);
  min-height: 100%;
}

.hero-card {
  border: 1px solid rgb(15 23 42 / 8%);
  border-radius: 20px;
  background: linear-gradient(135deg, rgb(255 255 255 / 95%), rgb(255 248 238 / 92%));
  box-shadow: 0 18px 45px rgb(15 23 42 / 8%);
  padding: 20px;
}

.hero-label {
  color: #64748b;
  display: block;
  font-size: 13px;
  margin-bottom: 10px;
}

.hero-value {
  color: #0f172a;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
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

.section-title {
  color: #0f172a;
  font-size: 15px;
  font-weight: 600;
}

.tag-list {
  align-items: flex-start;
  display: flex;
  flex-wrap: wrap;
}
</style>
