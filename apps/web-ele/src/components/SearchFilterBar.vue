<script setup lang="ts">
import { ref, watch } from "vue";

import {
  ElButton,
  ElCheckboxButton,
  ElCheckboxGroup,
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
} from "element-plus";

interface FilterOptions {
  platforms: string[];
  minPrice?: number;
  maxPrice?: number;
  sortBy: string;
  brand: string;
}

const props = defineProps<{
  initialFilters?: FilterOptions;
  initialKeyword?: string;
}>();

const emit = defineEmits<{
  (e: "search", keyword: string): void;
  (e: "filter", filters: FilterOptions): void;
}>();

const keyword = ref(props.initialKeyword || "");

// Sync keyword with prop change
watch(
  () => props.initialKeyword,
  (newVal) => {
    keyword.value = newVal || "";
  },
);
const filters = ref({
  platforms: props.initialFilters?.platforms || [],
  minPrice: props.initialFilters?.minPrice || undefined,
  maxPrice: props.initialFilters?.maxPrice || undefined,
  sortBy: props.initialFilters?.sortBy || "relevance",
  brand: props.initialFilters?.brand || "",
});

// Sync internal filters with props when they change (e.g. from URL)
watch(
  () => props.initialFilters,
  (newVal) => {
    if (newVal) {
      filters.value = {
        platforms: newVal.platforms || [],
        minPrice: newVal.minPrice || undefined,
        maxPrice: newVal.maxPrice || undefined,
        sortBy: newVal.sortBy || "relevance",
        brand: newVal.brand || "",
      };
    }
  },
  { deep: true },
);

const handleSearch = () => {
  emit("search", keyword.value);
};

const handleFilterChange = () => {
  emit("filter", filters.value);
};

const clearFilters = () => {
  filters.value = {
    platforms: [],
    minPrice: undefined,
    maxPrice: undefined,
    sortBy: "relevance",
    brand: "",
  };
  handleFilterChange();
};
</script>

<template>
  <div
    class="bg-white dark:bg-zinc-900 p-6 rounded-xl shadow-sm border border-gray-100 dark:border-zinc-800 mb-6"
  >
    <div class="flex gap-4 mb-6">
      <ElInput
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
          <ElButton type="primary" @click="handleSearch" class="search-btn">搜索全网</ElButton>
        </template>
      </ElInput>
    </div>

    <div class="flex flex-col gap-4">
      <!-- Primary Filters Row -->
      <div class="flex flex-wrap items-center gap-x-8 gap-y-4 text-sm">
        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-zinc-500 font-medium">平台:</span>
          <ElCheckboxGroup v-model="filters.platforms" size="small" @change="handleFilterChange">
            <ElCheckboxButton value="JD">京东</ElCheckboxButton>
            <ElCheckboxButton value="TM">天猫</ElCheckboxButton>
            <ElCheckboxButton value="PDD">拼多多</ElCheckboxButton>
          </ElCheckboxGroup>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-zinc-500 font-medium">价格区间:</span>
          <div class="flex items-center gap-1 w-48">
            <ElInputNumber
              v-model="filters.minPrice"
              placeholder="最低"
              size="small"
              :controls="false"
              class="w-full"
              @change="handleFilterChange"
            />
            <span class="text-gray-300 dark:text-zinc-600">-</span>
            <ElInputNumber
              v-model="filters.maxPrice"
              placeholder="最高"
              size="small"
              :controls="false"
              class="w-full"
              @change="handleFilterChange"
            />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-gray-500 dark:text-zinc-500 font-medium">品牌:</span>
          <ElSelect
            v-model="filters.brand"
            placeholder="全部品牌"
            size="small"
            clearable
            class="w-32"
            @change="handleFilterChange"
          >
            <ElOption label="Apple" value="Apple" />
            <ElOption label="Samsung" value="Samsung" />
            <ElOption label="Sony" value="Sony" />
            <ElOption label="Nintendo" value="Nintendo" />
          </ElSelect>
        </div>

        <div class="ml-auto flex items-center gap-3">
          <ElButton size="small" link @click="clearFilters">重置筛选</ElButton>
          <div class="h-4 w-[1px] bg-gray-200 dark:bg-zinc-800"></div>
          <ElSelect v-model="filters.sortBy" size="small" class="w-32" @change="handleFilterChange">
            <template #prefix>
              <span class="iconify lucide--filter-line mr-1"></span>
            </template>
            <ElOption label="综合排序" value="relevance" />
            <ElOption label="价格由低到高" value="price_asc" />
            <ElOption label="价格由高到低" value="price_desc" />
          </ElSelect>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-input :deep(.el-input-group__append) {
  padding: 0;
  background: transparent;
  border: none;
}

.search-btn {
  height: 100%;
  padding: 0 24px;
  margin: 0;
  border-radius: 0 8px 8px 0 !important;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 8px 0 0 8px;
  box-shadow: 0 0 0 1px #dcdfe6 inset !important;
}

.dark .search-input :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #4c4d4f inset !important;
}
</style>
