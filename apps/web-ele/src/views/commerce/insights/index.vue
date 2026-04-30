<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";

import { Page } from "@vben/common-ui";

import { ElButton, ElCard, ElEmpty, ElTag, ElTimeline, ElTimelineItem } from "element-plus";

import { getMarketInsightsApi } from "#/api/intelligence";

interface MarketInsight {
  id: string;
  type: string;
  label: string;
  title: string;
  description: string;
  severity: "danger" | "info" | "success" | "warning";
  product_id: number;
  timestamp: string;
  metadata: any;
}

const insights = ref<MarketInsight[]>([]);
const loading = ref(true);
const lastUpdated = ref(new Date());
const router = useRouter();
let timer: any = null;

const fetchInsights = async (isAutoRefresh = false) => {
  if (!isAutoRefresh) loading.value = true;
  try {
    const res = await getMarketInsightsApi(30);
    // 防御性赋值，确保即使 API 返回异常也是数组
    insights.value = res?.data || [];
    lastUpdated.value = new Date();
  } catch (error) {
    console.error("Failed to fetch market insights:", error);
    insights.value = [];
  } finally {
    loading.value = false;
  }
};

const handleViewProduct = (productId: number) => {
  router.push(`/commerce/detail/${productId}`); // 修正路由路径
};

onMounted(() => {
  fetchInsights();
  // Set up auto refresh every 30 seconds
  timer = setInterval(() => {
    fetchInsights(true);
  }, 30_000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

const getRelativeTime = (timestamp: string) => {
  if (!timestamp) return "未知时间";
  const now = new Date();
  const past = new Date(timestamp);
  const diff = Math.floor((now.getTime() - past.getTime()) / 1000);

  if (diff < 60) return "刚刚";
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
  if (diff < 86_400) return `${Math.floor(diff / 3600)}小时前`;
  return past.toLocaleDateString();
};
</script>

<template>
  <Page title="智能市场快报" description="实时监控全网市场动态，深度解析价格博弈与补货机会。">
    <template #extra>
      <div class="flex items-center gap-4">
        <span class="text-xs text-zinc-400 font-bold">最后更新: {{ lastUpdated.toLocaleTimeString() }}</span>
        <ElButton
          type="primary"
          plain
          size="small"
          :loading="loading"
          @click="() => fetchInsights()"
        >
          <span class="iconify lucide--refresh-cw mr-1"></span>
          强制刷新
        </ElButton>
      </div>
    </template>

    <div class="max-w-5xl mx-auto p-4">
      <!-- 修正：添加 insights 存在性检查 -->
      <div v-if="insights && insights.length > 0" class="space-y-6">
        <ElTimeline>
          <ElTimelineItem
            v-for="item in insights"
            :key="item.id"
            :timestamp="getRelativeTime(item.timestamp)"
            placement="top"
            :type="item.severity"
          >
            <ElCard
              shadow="hover"
              class="!rounded-2xl border-none mb-4 group cursor-pointer"
              @click="handleViewProduct(item.product_id)"
            >
              <div class="flex items-start justify-between">
                <div class="space-y-3 flex-grow">
                  <div class="flex items-center gap-2">
                    <ElTag
                      :type="item.severity"
                      size="small"
                      effect="dark"
                      class="!rounded-lg uppercase font-black tracking-widest text-[10px]"
                    >
                      {{ item.label }}
                    </ElTag>
                    <span
                      v-if="item.type === 'PRICE_DROP'"
                      class="text-green-500 font-black text-xs"
                    >
                      ⚡️ 发现购买时机
                    </span>
                    <span v-if="item.type === 'LOW_STOCK'" class="text-red-500 font-black text-xs">
                      🔥 补货迫在眉睫
                    </span>
                  </div>

                  <h3
                    class="text-lg font-black text-zinc-800 dark:text-zinc-100 group-hover:text-primary transition-colors"
                  >
                    {{ item.title }}
                  </h3>

                  <p class="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed max-w-2xl">
                    {{ item.description }}
                  </p>

                  <div class="flex items-center gap-6 pt-2">
                    <div v-if="item.metadata?.price" class="flex flex-col">
                      <span class="text-[10px] font-black text-zinc-400 uppercase">当前报盘</span>
                      <span class="text-sm font-black text-red-600 font-mono">¥{{ item.metadata.price }}</span>
                    </div>
                    <div v-if="item.metadata?.platform" class="flex flex-col">
                      <span class="text-[10px] font-black text-zinc-400 uppercase">源渠道</span>
                      <span class="text-sm font-black">{{ item.metadata.platform }}</span>
                    </div>
                    <div v-if="item.metadata?.stock !== undefined" class="flex flex-col">
                      <span class="text-[10px] font-black text-zinc-400 uppercase">剩余库存</span>
                      <span
                        class="text-sm font-black"
                        :class="item.metadata.stock < 10 ? 'text-red-600' : ''"
                        >{{ item.metadata.stock }}</span>
                    </div>
                  </div>
                </div>

                <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                  <ElButton circle type="primary" plain>
                    <span class="iconify lucide--chevron-right"></span>
                  </ElButton>
                </div>
              </div>
            </ElCard>
          </ElTimelineItem>
        </ElTimeline>
      </div>

      <div v-else-if="!loading" class="py-40 flex flex-col items-center">
        <ElEmpty description="市场一片宁静，暂无重大行情波动" />
        <p class="text-xs text-zinc-400 mt-4">AI Agent 正在持续扫描 50+ 个电商平台...</p>
      </div>
    </div>
  </Page>
</template>

<style scoped>
:deep(.el-card__body) {
  padding: 1.5rem;
}

.tracking-widest {
  letter-spacing: 0.1em;
}

:deep(.el-timeline-item__node) {
  border: 4px solid white;
  box-shadow: 0 0 10px rgb(0 0 0 / 10%);
}

.dark :deep(.el-timeline-item__node) {
  border: 4px solid #18181b;
}
</style>
