<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { Page } from "@vben/common-ui";

import { ElButton, ElEmpty } from "element-plus";

import { AnalyticsEvents, logAnalyticsEventApi } from "#/api/analytics";
import { searchProductsApi } from "#/api/product";
import ProductList from "#/components/ProductList.vue";
import SearchFilterBar from "#/components/SearchFilterBar.vue";

interface FilterState {
  sortBy: string;
  brand?: string;
  platforms: string[];
  minPrice?: number;
  maxPrice?: number;
}

const router = useRouter();
const route = useRoute();

// 内部状态托管
const keyword = ref((route.query.q as string) || "");
const activeFilters = ref<FilterState>({
  sortBy: (route.query.sort_by as string) || "relevance",
  brand: (route.query.brand as string) || undefined,
  platforms: Array.isArray(route.query.platforms)
    ? (route.query.platforms as string[])
    : (route.query.platforms
      ? [route.query.platforms as string]
      : []),
  minPrice: route.query.min_price ? Number(route.query.min_price) : undefined,
  maxPrice: route.query.max_price ? Number(route.query.max_price) : undefined,
});

const products = ref<any[]>([]);
const loading = ref(false);
const error = ref<null | string>(null);

// 执行搜索的核心函数
const performFetch = async () => {
  if (!keyword.value.trim()) {
    products.value = [];
    return;
  }

  loading.value = true;
  error.value = null;
  try {
    const res = await searchProductsApi({
      q: keyword.value,
      sort_by: activeFilters.value.sortBy,
      brand: activeFilters.value.brand,
      platforms: activeFilters.value.platforms,
      min_price: activeFilters.value.minPrice,
      max_price: activeFilters.value.maxPrice,
    });
    products.value = res.items || [];
  } catch (error_: any) {
    error.value = error_.message || "搜索失败，请刷新重试";
  } finally {
    loading.value = false;
  }
};

// 【核心优化】：手动同步 URL，但不触发路由导航（绝不开新页签）
const syncUrlSilently = () => {
  const url = new URL(window.location.href);
  url.searchParams.set("q", keyword.value);
  url.searchParams.set("sort_by", activeFilters.value.sortBy);

  if (activeFilters.value.brand) {
    url.searchParams.set("brand", activeFilters.value.brand);
  } else {
    url.searchParams.delete("brand");
  }

  // 处理数组
  url.searchParams.delete("platforms");
  activeFilters.value.platforms.forEach((p) => url.searchParams.append("platforms", p));

  if (activeFilters.value.minPrice)
    url.searchParams.set("min_price", activeFilters.value.minPrice.toString());
  else url.searchParams.delete("min_price");

  if (activeFilters.value.maxPrice)
    url.searchParams.set("max_price", activeFilters.value.maxPrice.toString());
  else url.searchParams.delete("max_price");

  // 使用 history 原生方法，绕过 Vue Router 的页签监控
  window.history.replaceState(null, "", url.toString());
};

const handleSearch = (newKeyword: string) => {
  keyword.value = newKeyword;
  syncUrlSilently();
  void logAnalyticsEventApi(AnalyticsEvents.SEARCH_TRIGGERED, { q: newKeyword });
  void performFetch();
};

const handleFilter = (filters: FilterState) => {
  activeFilters.value = { ...filters };
  syncUrlSilently();
  void performFetch();
};

const handleProductClick = (product: any) => {
  void logAnalyticsEventApi(AnalyticsEvents.SEARCH_RESULT_CLICK, {
    id: product.id,
    name: product.name,
    keyword: keyword.value,
  });
  router.push({
    name: "CommerceDetail",
    params: { id: product.product_id || product.id },
  });
};

const handleRetry = () => {
  void performFetch();
};

// 监听路由的变化（仅用于从外部跳转进来时同步）
watch(
  () => route.query.q,
  (newQ) => {
    if (newQ && newQ !== keyword.value) {
      keyword.value = newQ as string;
      void performFetch();
    }
  },
);

onMounted(() => {
  void performFetch();
});
</script>

<template>
  <Page title="比价搜索" description="搜索全网商品，获取最佳购买建议和价格趋势">
    <div class="space-y-6">
      <!-- 搜索和过滤栏 -->
      <SearchFilterBar
        :initial-keyword="keyword"
        :initial-filters="activeFilters"
        @search="handleSearch"
        @filter="handleFilter"
      />

      <!-- 结果展示 -->
      <div class="min-h-[400px]">
        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div v-for="i in 8" :key="i" class="bg-card h-80 rounded-xl animate-pulse border"></div>
        </div>

        <template v-else-if="error">
          <div class="py-20 text-center">
            <ElEmpty :description="error">
              <ElButton type="primary" @click="handleRetry">重试搜索</ElButton>
            </ElEmpty>
          </div>
        </template>

        <template v-else-if="products.length > 0">
          <div class="mb-4">
            <span class="text-sm text-muted-foreground">
              找到关于 "{{ keyword }}" 的 {{ products.length }} 个结果
            </span>
          </div>
          <ProductList :products="products" @click="handleProductClick" />
        </template>

        <template v-else-if="keyword">
          <div class="py-20 text-center">
            <ElEmpty description="未找到相关商品，请尝试更换关键词或过滤器" />
          </div>
        </template>

        <template v-else>
          <div class="py-20 text-center opacity-60">
            <div class="text-6xl mb-6">🔍</div>
            <h3 class="text-xl font-bold">开始探索全网底价</h3>
            <p class="text-muted-foreground mt-2">输入商品名称或粘贴链接，Decidely 为您智能研判</p>
          </div>
        </template>
      </div>
    </div>
  </Page>
</template>
