<script setup lang="ts">
import { onMounted, ref } from "vue";

import { ElButton, ElProgress, ElRadioButton, ElRadioGroup } from "element-plus";

import { getAnalyticsDashboardApi } from "#/api/analytics";

const loading = ref(true);
const stats = ref<any>(null);
const days = ref(7);

const clampPercentage = (value: number) => {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(100, value));
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await getAnalyticsDashboardApi(days.value);
    stats.value = res;
  } catch (error) {
    console.error("Dashboard fetch error:", error);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchData);
</script>

<template>
  <div class="analytics-container p-6 bg-zinc-50 dark:bg-zinc-950 min-h-screen">
    <div class="max-w-7xl mx-auto space-y-8">
      <!-- Header -->
      <div
        class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white dark:bg-zinc-900/50 backdrop-blur-xl p-8 rounded-3xl border border-zinc-200/50 dark:border-zinc-800/50 shadow-xl shadow-black/5"
      >
        <div>
          <h1
            class="text-3xl font-black text-zinc-900 dark:text-zinc-50 tracking-tight flex items-center gap-3"
          >
            <span class="iconify lucide--bar-chart-3 text-blue-600"></span>
            决策链路分析看板
          </h1>
          <p class="mt-1 text-zinc-500 font-medium">监测用户从搜索到购买的全链路转化数据</p>
        </div>
        <div class="flex items-center gap-4">
          <ElRadioGroup v-model="days" size="small" @change="fetchData">
            <ElRadioButton :value="1">今日</ElRadioButton>
            <ElRadioButton :value="7">近7天</ElRadioButton>
            <ElRadioButton :value="30">近30天</ElRadioButton>
          </ElRadioGroup>
          <ElButton type="primary" plain class="!rounded-xl" @click="fetchData">刷新数据</ElButton>
        </div>
      </div>

      <!-- Key Metrics -->
      <div v-loading="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div
          v-for="(val, key) in stats?.raw_counts || {}"
          :key="key"
          class="bg-white dark:bg-zinc-900 p-6 rounded-3xl border border-zinc-100 dark:border-zinc-800 shadow-sm hover:shadow-lg transition-all group"
        >
          <div
            class="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-1 group-hover:text-blue-500 transition-colors"
          >
            {{ key.replace(/_/g, " ") }}
          </div>
          <div class="text-3xl font-black text-zinc-900 dark:text-zinc-100 font-mono">
            {{ val }}
          </div>
        </div>

        <!-- Placeholder for empty stats -->
        <template v-if="!stats">
          <div
            v-for="i in 4"
            :key="i"
            class="h-28 bg-zinc-200 dark:bg-zinc-800 animate-pulse rounded-3xl"
          ></div>
        </template>
      </div>

      <!-- Funnel and Top Searches -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Conversion Funnel (M1-07) -->
        <div
          class="bg-white dark:bg-zinc-900 p-8 rounded-[40px] border border-zinc-100 dark:border-zinc-800 shadow-sm"
        >
          <h3
            class="text-lg font-black text-zinc-900 dark:text-zinc-100 mb-8 flex items-center gap-2"
          >
            <span class="iconify lucide--filter text-zinc-400"></span>
            核心转化漏斗
          </h3>

          <div class="space-y-10" v-if="stats?.funnel">
            <div class="relative">
              <div class="flex justify-between items-end mb-2">
                <span class="text-xs font-bold text-zinc-500">搜索 -> 详情点击 (CTR)</span>
                <span class="text-sm font-black text-blue-600">{{ stats.funnel.search_to_detail.toFixed(1) }}%</span>
              </div>
              <ElProgress
                :percentage="clampPercentage(stats.funnel.search_to_detail)"
                :stroke-width="12"
                :show-text="false"
                color="#2563eb"
              />
            </div>

            <div class="relative">
              <div class="flex justify-between items-end mb-2">
                <span class="text-xs font-bold text-zinc-500">详情 -> 去购买点击</span>
                <span class="text-sm font-black text-cyan-500">{{ stats.funnel.detail_to_buy.toFixed(1) }}%</span>
              </div>
              <ElProgress
                :percentage="clampPercentage(stats.funnel.detail_to_buy)"
                :stroke-width="12"
                :show-text="false"
                color="#0891b2"
              />
            </div>

            <div class="relative">
              <div class="flex justify-between items-end mb-2">
                <span class="text-xs font-bold text-zinc-500">详情 -> 提醒创建成功</span>
                <span class="text-sm font-black text-purple-500">{{ stats.funnel.detail_to_alert.toFixed(1) }}%</span>
              </div>
              <ElProgress
                :percentage="clampPercentage(stats.funnel.detail_to_alert)"
                :stroke-width="12"
                :show-text="false"
                color="#9333ea"
              />
            </div>
          </div>

          <div v-else class="h-64 flex items-center justify-center text-zinc-300 italic">
            暂无足够数据生成漏斗
          </div>
        </div>

        <!-- Top Searches (High Density) -->
        <div
          class="bg-zinc-900 text-zinc-100 p-8 rounded-[40px] shadow-2xl relative overflow-hidden"
        >
          <div
            class="absolute top-0 right-0 w-64 h-64 bg-blue-600/20 blur-[100px] rounded-full"
          ></div>

          <h3 class="text-lg font-black mb-8 flex items-center gap-2 relative z-10">
            <span class="iconify lucide--trending-up text-blue-400"></span>
            高频搜索词云 (前 5)
          </h3>

          <div class="space-y-4 relative z-10">
            <div
              v-for="(item, idx) in stats?.top_searches"
              :key="idx"
              class="flex items-center justify-between p-4 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 hover:bg-white/10 transition-colors"
            >
              <div class="flex items-center gap-4">
                <span
                  class="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-xs font-black text-zinc-400"
                  >{{ idx + 1 }}</span>
                <span class="font-black tracking-tight">{{ item.query }}</span>
              </div>
              <span class="text-xs font-bold text-zinc-500">{{ item.count }} 次记录</span>
            </div>

            <div v-if="!stats?.top_searches?.length" class="text-center py-20 text-zinc-600 italic">
              暂无搜索数据记录
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics-container {
  animation: fade-in 0.6s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.el-progress-bar__outer) {
  background-color: rgb(228 228 231 / 50%) !important;
}

.dark :deep(.el-progress-bar__outer) {
  background-color: rgb(63 63 70 / 50%) !important;
}
</style>
