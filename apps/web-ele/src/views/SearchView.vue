<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import SearchFilterBar from '#/components/SearchFilterBar.vue';
import ProductList from '#/components/ProductList.vue';
import { searchProductsApi } from '#/api/product';
import { ElMessage } from 'element-plus';

import { Page } from '@vben/common-ui';

const router = useRouter();
const route = useRoute();


const keyword = ref((route.query.q as string) || '');
const loading = ref(false);
const products = ref([]);

const handleSearch = async (newKeyword: string) => {
  if (!newKeyword) return;
  
  keyword.value = newKeyword;
  router.push({ query: { q: newKeyword } });
  
  loading.value = true;
  try {
    const res = await searchProductsApi({ q: newKeyword });
    products.value = res?.items || [];
  } catch (err: any) {
    ElMessage.error(err.message || '搜索失败');
  } finally {
    loading.value = false;
  }
};

const handleProductClick = (product: any) => {
  router.push({
    name: 'ProductDetail',
    query: { id: product.id }
  });
};

onMounted(() => {
  if (keyword.value) {
    handleSearch(keyword.value);
  }
});
</script>

<template>
  <Page title="比价搜索" description="搜索全网商品，获取最佳购买建议和价格趋势">
    <SearchFilterBar :initial-keyword="keyword" @search="handleSearch" />

    <div v-if="keyword" class="mb-4 text-sm text-gray-500 dark:text-zinc-400">
      找到关于 <span class="text-primary font-bold">"{{ keyword }}"</span> 的 {{ products.length }} 个结果
    </div>

    <ProductList :products="products" :loading="loading" @click="handleProductClick" />
  </Page>
</template>

<style scoped>
.text-primary {
  color: var(--el-color-primary);
}
</style>
