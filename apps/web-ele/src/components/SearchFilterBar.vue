<script setup lang="ts">
import { ref, watch } from "vue";

import {
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
    class="bg-white dark:bg-zinc-900/50 backdrop-blur-xl p-5 rounded-3xl shadow-xl shadow-blue-500/5 border border-gray-100 dark:border-zinc-800 mb-8"
  >
    <!-- Search Row -->
    <div class="flex gap-3 mb-6">
      <div class="relative flex-grow group">
        <div
          class="absolute inset-0 bg-primary/5 rounded-2xl blur-lg group-focus-within:bg-primary/10 transition-all"
        ></div>
        <ElInput
          v-model="keyword"
          placeholder="搜索您心仪的高客单商品..."
          class="modern-search-input"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <span class="iconify lucide--search ml-2 text-primary/60"></span>
          </template>
        </ElInput>
      </div>
      <button
        class="bg-primary hover:bg-primary/90 text-primary-foreground font-black px-8 rounded-2xl transition-all shadow-lg active:scale-95 flex items-center gap-2"
        @click="handleSearch"
      >
        搜索全网
      </button>
    </div>

    <!-- Filters Content -->
    <div class="flex flex-col gap-5">
      <div class="flex flex-wrap items-center gap-x-12 gap-y-5 text-[13px]">
        <!-- Platforms -->
        <div class="flex items-center gap-3">
          <span class="text-zinc-500 font-black uppercase tracking-wider text-[11px]">平台分布</span>
          <ElCheckboxGroup v-model="filters.platforms" size="small" @change="handleFilterChange">
            <ElCheckboxButton value="JD">京东</ElCheckboxButton>
            <ElCheckboxButton value="TM">天猫</ElCheckboxButton>
            <ElCheckboxButton value="PDD">拼多多</ElCheckboxButton>
          </ElCheckboxGroup>
        </div>

        <!-- Price Range -->
        <div class="flex items-center gap-3">
          <span class="text-zinc-500 font-black uppercase tracking-wider text-[11px]">价格预算</span>
          <div class="flex items-center gap-1.5 w-48">
            <ElInputNumber
              v-model="filters.minPrice"
              placeholder="最低"
              size="default"
              :controls="false"
              class="compact-number"
              @change="handleFilterChange"
            />
            <span class="text-zinc-300">/</span>
            <ElInputNumber
              v-model="filters.maxPrice"
              placeholder="最高"
              size="default"
              :controls="false"
              class="compact-number"
              @change="handleFilterChange"
            />
          </div>
        </div>

        <!-- Brand -->
        <div class="flex items-center gap-3">
          <span class="text-zinc-500 font-black uppercase tracking-wider text-[11px]">品牌偏好</span>
          <ElSelect
            v-model="filters.brand"
            placeholder="不限品牌"
            size="default"
            clearable
            class="w-36 select-clean"
            @change="handleFilterChange"
          >
            <ElOption label="Apple" value="Apple" />
            <ElOption label="Samsung" value="Samsung" />
            <ElOption label="Sony" value="Sony" />
            <ElOption label="Nintendo" value="Nintendo" />
          </ElSelect>
        </div>

        <!-- Right Side: Reset & Sort -->
        <div class="ml-auto flex items-center gap-5">
          <button
            class="text-[12px] font-bold text-zinc-400 hover:text-red-500 transition-colors flex items-center gap-1"
            @click="clearFilters"
          >
            <span class="iconify lucide--refresh-ccw w-3 h-3"></span>
            重置
          </button>

          <div class="h-4 w-[1px] bg-zinc-200 dark:bg-zinc-800"></div>

          <ElSelect
            v-model="filters.sortBy"
            size="default"
            class="w-40 select-clean"
            @change="handleFilterChange"
          >
            <template #prefix>
              <span class="iconify lucide--list-filter mr-1 text-primary"></span>
            </template>
            <ElOption label="智能推荐" value="relevance" />
            <ElOption label="价格由低到高" value="price_asc" />
            <ElOption label="价格由高到低" value="price_desc" />
          </ElSelect>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modern-search-input :deep(.el-input__wrapper) {
  height: 54px;
  padding-right: 12px;
  padding-left: 12px;
  background: white;
  border: 1px solid transparent;
  border-radius: 16px;
  box-shadow: none !important;
  transition: all 0.3s;
}

.dark .modern-search-input :deep(.el-input__wrapper) {
  background: hsl(var(--zinc-900));
}

.modern-search-input :deep(.el-input__wrapper.is-focus) {
  background: white;
  border-color: var(--el-color-primary-light-5);
}

.compact-number :deep(.el-input__wrapper) {
  background: hsl(var(--zinc-50));
  border: 1px solid hsl(var(--zinc-100));
  border-radius: 10px;
  box-shadow: none !important;
}

.dark .compact-number :deep(.el-input__wrapper) {
  background: hsl(var(--zinc-950));
  border-color: hsl(var(--zinc-800));
}

.select-clean :deep(.el-input__wrapper) {
  background: hsl(var(--zinc-100) / 50%);
  border: 1px solid transparent;
  border-radius: 10px;
  box-shadow: none !important;
}

.dark .select-clean :deep(.el-input__wrapper) {
  background: hsl(var(--zinc-800) / 50%);
}

:deep(.el-checkbox-button__inner) {
  margin-right: 4px;
  background: hsl(var(--zinc-100) / 50%);
  border: none !important;
  border-radius: 8px !important;
}

.dark :deep(.el-checkbox-button__inner) {
  background: hsl(var(--zinc-800) / 50%);
}

:deep(.el-checkbox-button.is-checked .el-checkbox-button__inner) {
  color: white !important;
  background-color: var(--el-color-primary) !important;
  box-shadow: 0 4px 12px var(--el-color-primary-light-7) !important;
}
</style>
