<script setup lang="ts">
import type { PriceAlert } from "#/api/types";

import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { Page } from "@vben/common-ui";

import { ElButton, ElEmpty, ElMessage, ElMessageBox } from "element-plus";

import { deletePriceAlertApi, getPriceAlertsApi } from "#/api/alert";
import { AnalyticsEvents, logAnalyticsEventApi } from "#/api/analytics";

const loading = ref(true);
const error = ref<null | string>(null);
const alerts = ref<PriceAlert[]>([]);

const fetchAlerts = async () => {
  loading.value = true;
  error.value = null;
  try {
    const res = await getPriceAlertsApi();
    alerts.value = res || [];
  } catch (error_: unknown) {
    const errMsg = error_ instanceof Error ? error_.message : "获取列表失败，请检查网络后重试";
    console.error("Fetch alerts error:", error_);
    error.value = errMsg;
  } finally {
    loading.value = false;
  }
};

const handleRetry = () => {
  fetchAlerts();
};

const handleDelete = (alert: PriceAlert) => {
  ElMessageBox.confirm("确定要取消此降价提醒吗？该设置将无法恢复。", "确认取消", {
    confirmButtonText: "确认取消",
    cancelButtonText: "暂不取消",
    confirmButtonClass: "!rounded-xl",
    cancelButtonClass: "!rounded-xl",
    type: "warning",
  }).then(async () => {
    try {
      await deletePriceAlertApi(alert.id);
      ElMessage.success("已成功移除监测任务");
      fetchAlerts();
    } catch (error_: unknown) {
      const errMsg = error_ instanceof Error ? error_.message : "操作失败";
      ElMessage.error(errMsg);
    }
  });
};

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  target.src =
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNDAwIDQwMCI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNmM2Y0ZjYiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IiM5Y2EzYWYiPkltYWdlIE5vdCBGb3VuZDwvdGV4dD48L3N2Zz4=";
};

const stats = computed(() => {
  return {
    monitoring: alerts.value.filter((a) => a.status === "monitoring").length,
    triggered: alerts.value.filter((a) => a.status === "triggered").length,
  };
});

const getDiffPercent = (alert: PriceAlert) => {
  const current = alert.current_price || alert.sku?.price || 0;
  if (!current) return 0;
  return ((current - alert.target_price) / current) * 100;
};

const isNearTarget = (alert: PriceAlert) => {
  if (alert.is_triggered) return false;
  const diff = getDiffPercent(alert);
  return diff > 0 && diff <= 5; // Within 5%
};

const router = useRouter();
const handleDetail = (alert: PriceAlert) => {
  // T1-03: 支持返回商品详情
  const pid = alert.sku?.product_id;
  if (pid) {
    void logAnalyticsEventApi(AnalyticsEvents.ALERT_RETURN_CLICK, {
      alert_id: alert.id,
      product_id: pid,
    });
    router.push({ name: "CommerceDetail", params: { id: pid } });
  }
};

onMounted(fetchAlerts);
</script>

<template>
  <Page title="监测实验室" description="管理您的智能降价动态，捕捉每一个买入时点">
    <div v-loading="loading" class="min-h-[400px]">
      <!-- List & Summary Header -->
      <div v-if="alerts.length > 0" class="space-y-8">
        <!-- Summary Strip -->
        <div class="flex gap-4">
          <div
            class="bg-primary/5 border border-primary/20 px-6 py-4 rounded-3xl flex items-center gap-4"
          >
            <div
              class="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white font-black text-lg"
            >
              {{ stats.monitoring }}
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-primary uppercase tracking-widest">活跃监测中</span>
              <span class="text-xs font-bold text-zinc-600 dark:text-zinc-400">正在全网扫描价格波动</span>
            </div>
          </div>
          <div
            class="bg-green-50/50 dark:bg-green-900/10 border border-green-200/50 dark:border-green-800/30 px-6 py-4 rounded-3xl flex items-center gap-4"
          >
            <div
              class="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center text-white font-black text-lg"
            >
              {{ stats.triggered }}
            </div>
            <div class="flex flex-col">
              <span class="text-[10px] font-black text-green-600 uppercase tracking-widest">已捕获降价</span>
              <span class="text-xs font-bold text-zinc-600 dark:text-zinc-400">系统已成功通过短信/邮件提醒</span>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="alert in alerts"
            :key="alert.id"
            class="relative flex flex-col bg-white dark:bg-zinc-900 rounded-3xl border border-gray-100 dark:border-zinc-800 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group overflow-hidden cursor-pointer"
            @click="handleDetail(alert)"
          >
            <!-- Badge -->
            <div class="absolute top-4 right-4 z-10">
              <div
                v-if="alert.status === 'triggered'"
                class="bg-green-500 text-white font-black text-[9px] px-3 py-1.5 rounded-full shadow-lg flex items-center gap-1 animate-bounce"
              >
                <span class="iconify lucide--sparkles w-3 h-3"></span>
                已命中
              </div>
              <div
                v-else-if="isNearTarget(alert)"
                class="bg-orange-500 text-white font-black text-[9px] px-3 py-1.5 rounded-full shadow-lg flex items-center gap-1 shadow-orange-500/20"
              >
                <div class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></div>
                即将触发
              </div>
              <div
                v-else
                class="bg-zinc-100 dark:bg-zinc-800 text-zinc-400 font-black text-[9px] px-3 py-1.5 rounded-full flex items-center gap-1"
              >
                <div class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                监测中
              </div>
            </div>

            <div class="p-6 pb-2 flex gap-4">
              <div
                class="w-24 h-24 rounded-2xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-100 dark:border-zinc-700/50 flex flex-col items-center justify-center p-2 group-hover:bg-primary/5 transition-colors"
              >
                <img
                  :src="alert.sku?.product?.main_image"
                  class="w-full h-full object-contain mix-blend-multiply dark:mix-blend-normal group-hover:scale-110 transition-transform duration-500"
                  @error="handleImageError"
                />
              </div>
              <div class="flex-grow min-w-0 pr-10">
                <div class="flex items-center gap-2 mb-1">
                  <span
                    :class="alert.sku?.platform === 'JD' ? 'text-red-600' : 'text-orange-500'"
                    class="text-[9px] font-black uppercase"
                    >{{ alert.sku?.platform }}</span>
                  <div class="w-1 h-1 rounded-full bg-zinc-300"></div>
                  <span class="text-[9px] font-black text-zinc-400 truncate">{{
                    alert.sku?.shop_name
                  }}</span>
                </div>
                <h3
                  class="text-xs font-black text-zinc-800 dark:text-zinc-100 line-clamp-2 leading-relaxed h-[2.8rem]"
                >
                  {{ alert.sku?.product?.name || "未知商品" }}
                </h3>
              </div>
            </div>

            <div class="px-6 py-4 flex-grow flex flex-col">
              <div
                class="rounded-2xl p-4 flex justify-between items-center transition-colors"
                :class="
                  isNearTarget(alert)
                    ? 'bg-orange-50 dark:bg-orange-950/20 border border-orange-100 dark:border-orange-900/30'
                    : 'bg-zinc-50 dark:bg-zinc-800/50 border border-transparent'
                "
              >
                <div class="flex flex-col">
                  <span class="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">目标成交价</span>
                  <span class="text-xl font-black text-red-600 font-mono tracking-tighter">¥{{ alert.target_price }}</span>
                </div>
                <div class="flex flex-col items-end">
                  <span class="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">当前低价</span>
                  <span
                    class="text-xl font-black text-zinc-800 dark:text-zinc-100 font-mono tracking-tighter"
                    >¥{{ alert.current_price || alert.sku?.price || 0 }}</span>
                </div>
              </div>

              <!-- Distance Bar (T1-02, T1-04) -->
              <div v-if="alert.status === 'monitoring'" class="mt-4 px-1 space-y-2">
                <div class="flex justify-between text-[9px] font-black uppercase tracking-tighter">
                  <span class="text-zinc-400">距离目标价还差</span>
                  <span :class="isNearTarget(alert) ? 'text-orange-500' : 'text-primary'">
                    ¥{{
                      ((alert.current_price || alert.sku?.price || 0) - alert.target_price).toFixed(
                        2,
                      )
                    }}
                    ({{ getDiffPercent(alert).toFixed(1) }}%)
                  </span>
                </div>
                <div class="h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    class="h-full transition-all duration-1000"
                    :class="isNearTarget(alert) ? 'bg-orange-500' : 'bg-primary'"
                    :style="{
                      width: `${Math.min(100, Math.max(0, 100 - getDiffPercent(alert)))}%`,
                    }"
                  ></div>
                </div>
                <div
                  v-if="alert.trigger_reason"
                  class="text-[10px] font-bold text-orange-500 mt-2 flex items-center gap-1"
                >
                  <span class="iconify lucide--info w-3 h-3"></span>
                  {{ alert.trigger_reason }}
                </div>
              </div>

              <!-- Triggered Info & Actions (R2-03, R2-04, R2-05) -->
              <div v-if="alert.status === 'triggered'" class="mt-4 space-y-3">
                <div
                  class="bg-green-500/10 border border-green-500/20 p-3 rounded-2xl flex items-center justify-between"
                >
                  <div class="flex flex-col">
                    <span class="text-[8px] font-black text-green-600 uppercase tracking-widest">触发价格</span>
                    <span
                      class="text-[14px] font-black text-green-700 dark:text-green-400 font-mono"
                      >¥{{ alert.triggered_price }}</span>
                  </div>
                  <div class="flex flex-col items-end">
                    <span class="text-[8px] font-black text-green-600 uppercase tracking-widest">触发日期</span>
                    <span class="text-[10px] font-black text-green-700 dark:text-green-400">{{
                      new Date(alert.triggered_at!).toLocaleDateString()
                    }}</span>
                  </div>
                </div>

                <div
                  v-if="alert.trigger_reason"
                  class="bg-green-50 dark:bg-green-900/10 text-[10px] font-bold text-green-600 p-2 rounded-xl border border-green-100 dark:border-green-900/30"
                >
                  {{ alert.trigger_reason }}
                </div>

                <div class="grid grid-cols-2 gap-2">
                  <a
                    v-if="alert.sku?.buy_url"
                    :href="alert.sku.buy_url"
                    target="_blank"
                    class="bg-red-600 hover:bg-red-700 text-white text-[10px] font-black py-2 rounded-xl flex items-center justify-center gap-1 transition-all stop-propagation"
                    @click.stop
                  >
                    <span class="iconify lucide--shopping-cart w-3 h-3"></span>
                    立即去购买
                  </a>
                  <button
                    class="bg-primary/10 hover:bg-primary/20 text-primary text-[10px] font-black py-2 rounded-xl flex items-center justify-center gap-1 transition-all stop-propagation"
                    @click.stop="
                      () =>
                        $router.push({
                          name: 'CommerceSearch',
                          query: { q: alert.sku?.product?.name },
                        })
                    "
                  >
                    <span class="iconify lucide--search w-3 h-3"></span>
                    找替代品
                  </button>
                </div>
              </div>
            </div>

            <div class="px-6 pb-6 pt-2 flex items-center justify-between mt-auto">
              <div class="flex items-center gap-2">
                <span class="text-[9px] font-black text-zinc-400 uppercase tracking-widest">
                  {{ new Date(alert.created_at).toLocaleDateString() }}
                </span>
                <div class="w-1 h-1 rounded-full bg-zinc-200"></div>
                <button
                  class="text-[9px] font-black text-primary hover:underline"
                  @click.stop="handleDetail(alert)"
                >
                  查看详情
                </button>
              </div>
              <button
                class="bg-zinc-100 dark:bg-zinc-800 hover:bg-red-50 hover:text-red-500 dark:hover:bg-red-900/10 text-[10px] font-black px-4 py-2 rounded-xl transition-all stop-propagation"
                @click.stop="handleDelete(alert)"
              >
                取消监测
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- States -->
      <div v-else-if="error && !loading" class="flex flex-col items-center justify-center py-40">
        <ElEmpty :description="error">
          <template #extra>
            <ElButton type="primary" class="!rounded-xl" @click="handleRetry">
              重新建立连接
            </ElButton>
          </template>
        </ElEmpty>
      </div>

      <div v-else-if="!loading" class="flex flex-col items-center justify-center py-40 text-center">
        <div
          class="w-16 h-16 bg-zinc-100 dark:bg-zinc-800 rounded-3xl flex items-center justify-center mb-6"
        >
          <span class="iconify lucide--bell-plus text-zinc-400 w-8 h-8"></span>
        </div>
        <h3 class="text-xl font-black text-zinc-800 dark:text-zinc-100 mb-2">实验室目前很安静</h3>
        <p class="text-sm font-bold text-zinc-500 mb-8 max-w-xs">
          快去搜索您心仪的商品，我们会 24 小时为您盯盘，绝不错过任何神价。
        </p>
        <ElButton
          type="primary"
          class="!rounded-2xl !px-10 !py-6 !text-lg font-black"
          @click="() => $router.push('/commerce/search')"
        >
          开启首次监测
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
