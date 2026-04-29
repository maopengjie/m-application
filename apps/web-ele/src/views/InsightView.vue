<script setup lang="ts">
import type { InsightEvent } from "#/api/types";

import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { Page } from "@vben/common-ui";

import { ElButton, ElEmpty, ElTag } from "element-plus";

import { AnalyticsEvents, logAnalyticsEventApi } from "#/api/analytics";
import { getAggregatedInsightsApi } from "#/api/insight";

const loading = ref(true);
const error = ref<null | string>(null);
const insights = ref<InsightEvent[]>([]);
const summary = ref("");

const fetchInsights = async () => {
  loading.value = true;
  error.value = null;
  try {
    const res = await getAggregatedInsightsApi();
    insights.value = res.events || [];
    summary.value = res.summary;

    void logAnalyticsEventApi(AnalyticsEvents.INSIGHT_PAGE_VIEW, {
      event_count: insights.value.length,
    });
  } catch (error_: unknown) {
    const errMsg = error_ instanceof Error ? error_.message : "获取异动信息失败";
    console.error("Fetch insights error:", error_);
    error.value = errMsg;
  } finally {
    loading.value = false;
  }
};

const router = useRouter();
const handleDetail = (event: InsightEvent) => {
  void logAnalyticsEventApi(AnalyticsEvents.INSIGHT_EVENT_CLICK, {
    event_id: event.id,
    event_type: event.event_type,
    product_id: event.product_id,
  });
  router.push({ name: "CommerceDetail", params: { id: event.product_id } });
};

const getEventColor = (type: string) => {
  switch (type) {
    case "ALERT_HIT": {
      return "danger";
    }
    case "HIST_LOW": {
      return "warning";
    }
    case "PRICE_DROP": {
      return "success";
    }
    case "RISK_CHANGE": {
      return "info";
    }
    default: {
      return "primary";
    }
  }
};

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  target.src =
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNDAwIDQwMCI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNmM2Y0ZjYiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IiM5Y2EzYWYiPkltYWdlIE5vdCBGb3VuZDwvdGV4dD48L3N2Zz4=";
};

onMounted(fetchInsights);
</script>

<template>
  <Page title="今日异动情报" :description="summary || '全天候监测您的关注商品，捕捉每一个价值瞬间'">
    <div v-loading="loading" class="min-h-[400px] max-w-5xl mx-auto py-8">
      <div v-if="insights.length > 0" class="space-y-6">
        <div
          v-for="event in insights"
          :key="event.id"
          class="bg-white dark:bg-zinc-900 rounded-3xl border border-gray-100 dark:border-zinc-800 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden cursor-pointer flex flex-col md:flex-row gap-6 p-6"
          @click="handleDetail(event)"
        >
          <!-- Left: Image & Platform -->
          <div
            class="w-full md:w-32 h-32 flex-shrink-0 bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl flex items-center justify-center p-2 relative"
          >
            <img
              :src="event.image"
              class="max-w-full max-h-full object-contain"
              @error="handleImageError"
            />
            <div
              v-if="event.platform"
              class="absolute -bottom-2 -right-2 bg-white dark:bg-zinc-800 px-2 py-1 rounded-lg shadow-sm border border-zinc-100 dark:border-zinc-700 text-[10px] font-black text-zinc-500"
            >
              {{ event.platform }}
            </div>
          </div>

          <!-- Middle: Content -->
          <div class="flex-grow flex flex-col justify-between py-1">
            <div class="space-y-2">
              <div class="flex items-center gap-3">
                <ElTag
                  :type="getEventColor(event.event_type)"
                  size="small"
                  effect="dark"
                  class="!px-3 !rounded-full !border-none font-black text-[10px] uppercase"
                >
                  {{ event.title }}
                </ElTag>
                <span class="text-[10px] font-bold text-zinc-400">
                  {{
                    new Date(event.timestamp).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  }}
                </span>
              </div>
              <h3 class="text-lg font-black text-zinc-800 dark:text-zinc-100 leading-tight">
                {{ event.description }}
              </h3>
            </div>

            <div class="flex items-center gap-4 mt-4 md:mt-0">
              <div class="flex flex-col">
                <span class="text-[9px] font-black text-zinc-400 tracking-widest uppercase mb-0.5">参考当前价</span>
                <span class="text-xl font-black text-red-600 font-mono tracking-tighter">¥{{ event.current_price }}</span>
              </div>
              <div v-if="event.diff_percent" class="flex flex-col">
                <span class="text-[9px] font-black text-zinc-400 tracking-widest uppercase mb-0.5">异动幅度</span>
                <span class="text-xl font-black text-green-500 font-mono tracking-tighter">{{ event.diff_percent.toFixed(1) }}%</span>
              </div>
            </div>
          </div>

          <!-- Right: Action -->
          <div
            class="flex items-center justify-center md:border-l border-zinc-100 dark:border-zinc-800 md:pl-10"
          >
            <button
              class="bg-primary/5 hover:bg-primary/10 text-primary p-4 rounded-full transition-all group active:scale-90"
            >
              <span
                class="iconify lucide--chevron-right w-6 h-6 group-hover:translate-x-1 transition-transform"
              ></span>
            </button>
          </div>
        </div>
      </div>

      <!-- States -->
      <div v-else-if="error && !loading" class="flex flex-col items-center justify-center py-40">
        <ElEmpty :description="error">
          <template #extra>
            <ElButton type="primary" @click="fetchInsights">重新尝试加载</ElButton>
          </template>
        </ElEmpty>
      </div>

      <div v-else-if="!loading" class="flex flex-col items-center justify-center py-40 text-center">
        <div class="w-20 h-20 bg-primary/5 rounded-full flex items-center justify-center mb-6">
          <span class="iconify lucide--bell-off text-primary w-10 h-10"></span>
        </div>
        <h3 class="text-xl font-black text-zinc-800 dark:text-zinc-100 mb-2">今天还没有重大异动</h3>
        <p class="text-sm font-bold text-zinc-500 mb-8 max-w-xs">
          如果您关注的商品出现了降价、风险异常或历史低价，我们会第一时间汇聚于此。
        </p>
        <ElButton
          type="primary"
          class="!rounded-2xl !px-10 !py-6 !text-lg font-black"
          @click="() => $router.push('/commerce/search')"
        >
          去关注更多商品
        </ElButton>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.tracking-widest {
  letter-spacing: 0.1em;
}

.tracking-tighter {
  letter-spacing: -0.05em;
}
</style>
