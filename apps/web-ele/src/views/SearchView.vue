<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import SearchFilterBar from '#/components/SearchFilterBar.vue';
import ProductList from '#/components/ProductList.vue';
import { searchProductsApi } from '#/api/product';
import { ElMessage } from 'element-plus';

import { Page } from '@vben/common-ui';

import type { Product } from '#/api/types';

const router = useRouter();
const route = useRoute();

interface FilterState {
  sortBy: string;
  platforms: string[];
  minPrice?: number;
  maxPrice?: number;
  brand: string;
}

const keyword = ref((route.query.q as string) || '');
const activeFilters = ref<FilterState>({
  sortBy: (route.query.sort_by as string) || 'relevance',
  platforms: route.query.platforms ? (Array.isArray(route.query.platforms) ? (route.query.platforms as string[]) : [route.query.platforms as string]) : [],
  minPrice: route.query.min_price ? Number(route.query.min_price) : undefined,
  maxPrice: route.query.max_price ? Number(route.query.max_price) : undefined,
  brand: (route.query.brand as string) || ''
});
const loading = ref(false);
const error = ref<string | null>(null);
const products = ref<Product[]>([]);

const performSearch = async () => {
  const kw = route.query.q as string;
  if (!kw) return;
  
  loading.value = true;
  error.value = null;
  
  // Extract filters from URL
  const searchParams = {
    q: kw,
    sort_by: (route.query.sort_by as string) === 'relevance' ? undefined : (route.query.sort_by as string),
    platforms: route.query.platforms ? (Array.isArray(route.query.platforms) ? route.query.platforms : [route.query.platforms]) : undefined,
    min_price: route.query.min_price ? Number(route.query.min_price) : undefined,
    max_price: route.query.max_price ? Number(route.query.max_price) : undefined,
    brand: (route.query.brand as string) || undefined,
  };
  
  try {
    const res = await searchProductsApi(searchParams);
    products.value = res?.items || [];
  } catch (err: unknown) {
    const errMsg = err instanceof Error ? err.message : '搜索请求失败，请检查网络后重试';
    console.error('Search error:', err);
    error.value = errMsg;
  } finally {
    loading.value = false;
  }
};

const handleSearch = (newKeyword: string, newFilters?: Partial<FilterState>) => {
  const combinedFilters = {
    ...activeFilters.value,
    ...(newFilters || {})
  };
  
  // Just update the URL. The watch will handle the rest.
  router.push({ 
    query: { 
      q: newKeyword, 
      sort_by: combinedFilters.sortBy,
      brand: combinedFilters.brand || undefined,
      platforms: combinedFilters.platforms.length ? combinedFilters.platforms : undefined,
      min_price: combinedFilters.minPrice,
      max_price: combinedFilters.maxPrice,
    } 
  });
};

const handleRetry = () => {
  performSearch();
};

const handleFilter = (filters: FilterState) => {
  handleSearch(keyword.value, filters);
};

const handleProductClick = (product: Product) => {
  router.push({
    name: 'CommerceDetail',
    params: { id: product.product_id }
  });
};

watch(
  () => route.query,
  (newQuery) => {
    // Sync state
    keyword.value = (newQuery.q as string) || '';
    activeFilters.value = {
      sortBy: (newQuery.sort_by as string) || 'relevance',
      platforms: newQuery.platforms ? (Array.isArray(newQuery.platforms) ? newQuery.platforms : [newQuery.platforms]) : [],
      minPrice: newQuery.min_price ? Number(newQuery.min_price) : undefined,
      maxPrice: newQuery.max_price ? Number(newQuery.max_price) : undefined,
      brand: (newQuery.brand as string) || ''
    };
    
    // Fetch data
    performSearch();
  },
  { deep: true, immediate: true }
);

onMounted(() => {
  // performSearch handled by immediate watch
});
</script>

<template>
  <Page title="比价搜索" description="搜索全网商品，获取最佳购买建议和价格趋势">
    <SearchFilterBar 
      :initial-keyword="keyword" 
      :initial-filters="activeFilters"
      @search="handleSearch" 
      @filter="handleFilter"
    />

    <div v-if="keyword" class="mb-4 text-sm text-gray-500 dark:text-zinc-400">
      找到关于 <span class="text-primary font-bold">"{{ keyword }}"</span> 的 {{ products.length }} 个结果
    </div>

    <div v-if="error && !loading" class="flex flex-col items-center justify-center py-20">
      <el-empty :description="error">
        <template #extra>
          <el-button type="primary" @click="handleRetry">重试搜索</el-button>
        </template>
      </el-empty>
    </div>

    <ProductList v-else :products="products" :loading="loading" @click="handleProductClick" />
  </Page>
</template>

<style scoped>
.text-primary {
  color: var(--el-color-primary);
}
</style>
