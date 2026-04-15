<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { searchProductsApi } from '#/api/product';
import { ElMessage } from 'element-plus';
import { Search } from '@element-plus/icons-vue';

const router = useRouter();
const query = ref('');
const loading = ref(false);
const products = ref<any[]>([]);

const handleSearch = async () => {
  if (!query.value.trim()) {
    ElMessage.warning('请输入搜索关键词');
    return;
  }
  loading.value = true;
  try {
    const res = await searchProductsApi({ q: query.value });
    products.value = res.items || [];
  } catch (error) {
    console.error('Search failed:', error);
    ElMessage.error('搜索失败');
  } finally {
    loading.value = false;
  }
};

const goToDetail = (id: number) => {
  router.push(`/commerce/detail/${id}`);
};

onMounted(() => {
  // Optional: initial search or load popular items
});
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">
    <!-- Header / Search Bar -->
    <div class="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 mb-8">
      <h1 class="text-2xl font-bold text-gray-800 mb-6 text-center">智能购物搜索</h1>
      <div class="flex gap-4 max-w-3xl mx-auto">
        <el-input
          v-model="query"
          placeholder="搜索商品名称、品牌或分类 (例如: iPhone, 手机...)"
          size="large"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" size="large" :loading="loading" @click="handleSearch" class="px-10">
          搜索
        </el-button>
      </div>
    </div>

    <!-- Results -->
    <div v-loading="loading">
      <div v-if="products.length > 0" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <div
          v-for="item in products"
          :key="item.id"
          class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow cursor-pointer flex flex-col"
          @click="goToDetail(item.id)"
        >
          <div class="aspect-square bg-gray-50 flex items-center justify-center p-4">
            <img :src="item.main_image" :alt="item.name" class="max-h-full object-contain">
          </div>
          <div class="p-4 flex-1 flex flex-col">
            <div class="text-xs text-blue-600 font-medium mb-1">{{ item.brand || '未标注品牌' }}</div>
            <h3 class="text-gray-800 font-medium mb-2 line-clamp-2 h-12">{{ item.name }}</h3>
            <div class="mt-auto flex items-baseline gap-1">
              <span class="text-xs text-red-500 font-bold">¥</span>
              <span class="text-xl text-red-500 font-bold">{{ item.min_price }}</span>
              <span class="text-xs text-gray-400 ml-1">起</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!loading" class="text-center py-32 bg-white rounded-2xl border border-dashed border-gray-200">
        <el-empty description="暂无搜索结果，换个词试试吧" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
