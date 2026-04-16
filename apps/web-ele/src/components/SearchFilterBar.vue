<script setup lang="ts">
import { ref, watch } from 'vue';
import { 
  ElInput, 
  ElButton, 
  ElRadioGroup, 
  ElRadioButton, 
  ElInputNumber, 
  ElSelect, 
  ElOption,
  ElCheckboxButton,
  ElCheckboxGroup
} from 'element-plus';

interface FilterOptions {
  platforms: string[];
  minPrice?: number;
  maxPrice?: number;
  sortBy: string;
  brand: string;
}

const props = defineProps<{
  initialKeyword?: string;
  initialFilters?: FilterOptions;
}>();

const emit = defineEmits<{
  (e: 'search', keyword: string): void;
  (e: 'filter', filters: FilterOptions): void;
}>();

const keyword = ref(props.initialKeyword || '');

// Sync keyword with prop change
watch(() => props.initialKeyword, (newVal) => {
  keyword.value = newVal || '';
});
const filters = ref({
  platforms: props.initialFilters?.platforms || [],
  minPrice: props.initialFilters?.minPrice || undefined,
  maxPrice: props.initialFilters?.maxPrice || undefined,
  sortBy: props.initialFilters?.sortBy || 'relevance',
  brand: props.initialFilters?.brand || ''
});

// Sync internal filters with props when they change (e.g. from URL)
watch(() => props.initialFilters, (newVal) => {
  if (newVal) {
    filters.value = {
      platforms: newVal.platforms || [],
      minPrice: newVal.minPrice || undefined,
      maxPrice: newVal.maxPrice || undefined,
      sortBy: newVal.sortBy || 'relevance',
      brand: newVal.brand || ''
    };
  }
}, { deep: true });

const handleSearch = () => {
  emit('search', keyword.value);
};

const handleFilterChange = () => {
  emit('filter', filters.value);
};

const clearFilters = () => {
  filters.value = {
    platforms: [],
    minPrice: undefined,
    maxPrice: undefined,
    sortBy: 'relevance',
    brand: ''
  };
  handleFilterChange();
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
          <span class="iconify lucide--search mr-1 text-gray-400"></span>
        </template>
        <template #append>
          <el-button type="primary" @click="handleSearch" class="search-btn">搜索全网</el-button>
        </template>
      </el-input>
    </div>

    <div class="flex flex-col gap-4">
      <!-- Primary Filters Row -->
      <div class="flex flex-wrap items-center gap-x-8 gap-y-4 text-sm">
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-zinc-500 font-medium">平台:</span>
          <el-checkbox-group v-model="filters.platforms" size="small" @change="handleFilterChange">
            <el-checkbox-button value="JD">京东</el-checkbox-button>
            <el-checkbox-button value="TM">天猫</el-checkbox-button>
            <el-checkbox-button value="PDD">拼多多</el-checkbox-button>
          </el-checkbox-group>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-zinc-500 font-medium">价格区间:</span>
          <div class="flex items-center gap-1 w-48">
            <el-input-number v-model="filters.minPrice" placeholder="最低" size="small" :controls="false" class="w-full" @change="handleFilterChange" />
            <span class="text-gray-300 dark:text-zinc-600">-</span>
            <el-input-number v-model="filters.maxPrice" placeholder="最高" size="small" :controls="false" class="w-full" @change="handleFilterChange" />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-zinc-500 font-medium">品牌:</span>
          <el-select v-model="filters.brand" placeholder="全部品牌" size="small" clearable class="w-32" @change="handleFilterChange">
            <el-option label="Apple" value="Apple" />
            <el-option label="Samsung" value="Samsung" />
            <el-option label="Sony" value="Sony" />
            <el-option label="Nintendo" value="Nintendo" />
          </el-select>
        </div>

        <div class="ml-auto flex items-center gap-3">
          <el-button size="small" link @click="clearFilters">重置筛选</el-button>
          <div class="h-4 w-[1px] bg-gray-200 dark:bg-zinc-800"></div>
          <el-select v-model="filters.sortBy" size="small" class="w-32" @change="handleFilterChange">
            <template #prefix>
              <span class="iconify lucide--filter-line mr-1"></span>
            </template>
            <el-option label="综合排序" value="relevance" />
            <el-option label="价格由低到高" value="price_asc" />
            <el-option label="价格由高到低" value="price_desc" />
          </el-select>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-input :deep(.el-input-group__append) {
  padding: 0;
  border: none;
  background: transparent;
}

.search-btn {
  height: 100%;
  border-radius: 0 8px 8px 0 !important;
  margin: 0;
  padding: 0 24px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 8px 0 0 8px;
  box-shadow: 0 0 0 1px #dcdfe6 inset !important;
}

.dark .search-input :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #4c4d4f inset !important;
}
</style>
