<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  initialKeyword?: string;
}>();

const emit = defineEmits<{
  (e: 'search', keyword: string): void;
  (e: 'filter', filters: any): void;
}>();

const keyword = ref(props.initialKeyword || '');
const filters = ref({
  platform: '',
  minPrice: undefined,
  maxPrice: undefined,
  sortBy: 'relevance'
});

const handleSearch = () => {
  emit('search', keyword.value);
};

const handleFilterChange = () => {
  emit('filter', filters.value);
};
</script>

<template>
  <div class="bg-white dark:bg-zinc-900 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-zinc-800 mb-6">
    <div class="flex gap-4 mb-6">
      <el-input
        v-model="keyword"
        placeholder="输入商品名称或粘贴搜索链接..."
        class="search-input"
        clearable
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <span class="iconify lucide--search mr-1"></span>
        </template>
        <template #append>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </template>
      </el-input>
    </div>

    <div class="flex flex-wrap items-center gap-6 text-sm">
      <div class="flex items-center gap-2">
        <span class="text-gray-500 dark:text-zinc-400">平台:</span>
        <el-radio-group v-model="filters.platform" size="small" @change="handleFilterChange">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="JD">京东</el-radio-button>
          <el-radio-button label="TM">天猫</el-radio-button>
          <el-radio-button label="PDD">拼多多</el-radio-button>
        </el-radio-group>
      </div>

      <div class="flex items-center gap-2">
        <span class="text-gray-500 dark:text-zinc-400">价格区间:</span>
        <div class="flex items-center gap-1 w-48">
          <el-input-number v-model="filters.minPrice" placeholder="最低" size="small" :controls="false" class="w-full" />
          <span class="text-gray-300 dark:text-zinc-600">-</span>
          <el-input-number v-model="filters.maxPrice" placeholder="最高" size="small" :controls="false" class="w-full" />
        </div>
      </div>

      <div class="ml-auto">
        <el-select v-model="filters.sortBy" size="small" class="w-28" @change="handleFilterChange">
          <el-option label="综合排序" value="relevance" />
          <el-option label="价格最低" value="price_asc" />
          <el-option label="评价数" value="comments" />
        </el-select>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-input :deep(.el-input-group__append) {
  color: white;
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 8px 0 0 8px;
}
</style>
