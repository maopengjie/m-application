<script setup lang="ts">
import type { UserFollow } from "#/api/types";

import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { Page } from "@vben/common-ui";

import { ElButton, ElEmpty, ElMessage, ElMessageBox } from "element-plus";

import { AnalyticsEvents, logAnalyticsEventApi } from "#/api/analytics";
import { getFollowListApi, unfollowProductApi } from "#/api/product";

const loading = ref(true);
const error = ref<null | string>(null);
const follows = ref<UserFollow[]>([]);

const fetchFollows = async () => {
  loading.value = true;
  error.value = null;
  try {
    const res = await getFollowListApi();
    follows.value = res || [];
  } catch (error_: unknown) {
    const errMsg = error_ instanceof Error ? error_.message : "获取列表失败，请检查网络后重试";
    console.error("Fetch follows error:", error_);
    error.value = errMsg;
  } finally {
    loading.value = false;
  }
};

const handleRetry = () => {
  fetchFollows();
};

const handleUnfollow = (follow: UserFollow) => {
  ElMessageBox.confirm("确定要取消关注这个商品吗？", "确认取消", {
    confirmButtonText: "确认取消",
    cancelButtonText: "暂不取消",
    confirmButtonClass: "!rounded-xl",
    cancelButtonClass: "!rounded-xl",
    type: "warning",
  }).then(async () => {
    try {
      await unfollowProductApi(follow.product_id);
      ElMessage.success("已成功移出关注列表");
      fetchFollows();
    } catch (error_: unknown) {
      const errMsg = error_ instanceof Error ? error_.message : "操作失败";
      ElMessage.error(errMsg);
    }
  });
};

const router = useRouter();
const handleDetail = (follow: UserFollow) => {
  void logAnalyticsEventApi(AnalyticsEvents.FOLLOW_LIST_DETAIL_CLICK, {
    product_id: follow.product_id,
    product_name: follow.product.name,
  });
  router.push({ name: "CommerceDetail", params: { id: follow.product_id } });
};

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement;
  target.src =
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iNDAwIiB2aWV3Qm94PSIwIDAgNDAwIDQwMCI+PHJlY3Qgd2lkdGg9IjQwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiNmM2Y0ZjYiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9InNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjAiIGZpbGw9IiM5Y2EzYWYiPkltYWdlIE5vdCBGb3VuZDwvdGV4dD48L3N2Zz4=";
};

onMounted(fetchFollows);
</script>

<template>
  <Page title="我的关注" description="持续追踪您心仪商品的动态与价格变化">
    <div v-loading="loading" class="min-h-[400px]">
      <div v-if="follows.length > 0" class="space-y-8">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <div
            v-for="follow in follows"
            :key="follow.id"
            class="relative flex flex-col bg-white dark:bg-zinc-900 rounded-3xl border border-gray-100 dark:border-zinc-800 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group overflow-hidden cursor-pointer"
            @click="handleDetail(follow)"
          >
            <!-- Badge -->
            <div class="absolute top-4 right-4 z-10 flex flex-col gap-2 items-end">
              <div
                v-if="follow.is_near_low"
                class="bg-orange-600 text-white font-black text-[9px] px-3 py-1.5 rounded-full shadow-lg flex items-center gap-1 animate-pulse border border-orange-400"
              >
                <span class="iconify lucide--flame w-3 h-3"></span>
                历史极低
              </div>
              <div
                class="bg-blue-600 text-white font-black text-[9px] px-3 py-1.5 rounded-full shadow-lg flex items-center gap-1 border border-blue-400"
              >
                <span class="iconify lucide--heart w-3 h-3 fill-white"></span>
                追踪中
              </div>
            </div>

            <div class="p-6 pb-2">
              <div
                class="w-full aspect-square rounded-2xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-100 dark:border-zinc-700/50 flex flex-col items-center justify-center p-4 group-hover:bg-primary/5 transition-colors"
              >
                <img
                  :src="follow.product.main_image"
                  class="w-full h-full object-contain mix-blend-multiply dark:mix-blend-normal group-hover:scale-110 transition-transform duration-500"
                  @error="handleImageError"
                />
              </div>
              <div class="mt-4 min-w-0 pr-2">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-[9px] font-black text-zinc-400 uppercase tracking-widest">{{
                    follow.product.brand
                  }}</span>
                  <div class="w-1 h-1 rounded-full bg-zinc-300"></div>
                  <span class="text-[9px] font-black text-zinc-400 truncate">{{
                    follow.product.category
                  }}</span>
                </div>
                <h3
                  class="text-sm font-black text-zinc-800 dark:text-zinc-100 line-clamp-2 leading-tight h-[2.5rem]"
                >
                  {{ follow.product.name }}
                </h3>
              </div>
            </div>

            <div class="px-6 py-4 flex-grow flex flex-col gap-3">
              <div
                class="bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl p-4 flex justify-between items-center border border-zinc-100 dark:border-zinc-700/50"
              >
                <div class="flex flex-col">
                  <span class="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">当前底价</span>
                  <span class="text-xl font-black text-red-600 font-mono tracking-tighter">¥{{ follow.product.final_price || follow.product.min_price || "---" }}</span>
                </div>
                <div class="flex flex-col items-end">
                  <span class="text-[9px] font-black text-zinc-400 uppercase tracking-widest mb-1">价格动态</span>
                  <span
                    class="text-xs font-black"
                    :class="
                      follow.price_change_percent && follow.price_change_percent < 0
                        ? 'text-green-500'
                        : 'text-zinc-500'
                    "
                  >
                    {{
                      follow.price_change_percent
                        ? `${
                            (follow.price_change_percent > 0 ? "+" : "") +
                            follow.price_change_percent.toFixed(1)
                          }%`
                        : "平稳"
                    }}
                  </span>
                </div>
              </div>

              <div class="flex items-center justify-between px-1 translate-y-[-4px]">
                <div class="flex items-center gap-2">
                  <div
                    class="w-2 h-2 rounded-full"
                    :class="{
                      'bg-green-500':
                        follow.risk_status === '安全' || follow.risk_status === '正常',
                      'bg-orange-500': follow.risk_status === '警告',
                      'bg-red-500': follow.risk_status === '高风险',
                    }"
                  ></div>
                  <span class="text-[10px] font-black text-zinc-500 uppercase">{{
                    follow.risk_status || "正常"
                  }}</span>
                </div>
                <div class="text-[9px] font-black text-primary italic uppercase tracking-tighter">
                  {{ follow.current_status_text }}
                </div>
              </div>
            </div>

            <div class="px-6 pb-6 pt-0 flex items-center justify-between mt-auto">
              <span class="text-[9px] font-black text-zinc-400 uppercase tracking-widest">
                开启追踪: {{ new Date(follow.created_at).toLocaleDateString() }}
              </span>
              <button
                class="hover:text-red-500 text-[10px] font-black px-2 py-1 transition-all stop-propagation"
                @click.stop="handleUnfollow(follow)"
              >
                取消关注
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
              重新尝试加载
            </ElButton>
          </template>
        </ElEmpty>
      </div>

      <div v-else-if="!loading" class="flex flex-col items-center justify-center py-40 text-center">
        <div
          class="w-20 h-20 bg-blue-50 dark:bg-blue-900/10 rounded-full flex items-center justify-center mb-6"
        >
          <span class="iconify lucide--heart text-blue-400 w-10 h-10"></span>
        </div>
        <h3 class="text-xl font-black text-zinc-800 dark:text-zinc-100 mb-2">还没有关注任何商品</h3>
        <p class="text-sm font-bold text-zinc-500 mb-8 max-w-xs">
          在这里追踪您感兴趣的商品，我们会实时同步它们的全网价格波动与风险状态。
        </p>
        <ElButton
          type="primary"
          class="!rounded-2xl !px-10 !py-6 !text-lg font-black"
          @click="() => $router.push('/commerce/search')"
        >
          发现心动商品
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
