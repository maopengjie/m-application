<script setup lang="ts">
import type { Coupon } from "#/api/types";

import { onMounted, ref } from "vue";

import { Page } from "@vben/common-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@vben-core/shadcn-ui";

import { ElButton, ElEmpty, ElInputNumber, ElMessage, ElOption, ElSelect } from "element-plus";
import { ArrowRight, Tag, TicketPercent } from "lucide-vue-next";

import { getCouponsApi } from "#/api/coupon";

const coupons = ref<Coupon[]>([]);
const loading = ref(true);
const error = ref<null | string>(null);

// Claim state
const claimingId = ref<null | number>(null);
const claimedCoupons = ref<Set<number>>(new Set());

// Calculator state
const calcAmount = ref<number>(0);
const calcPlatform = ref("ALL");
const calcResults = ref<null | {
  appliedCoupons: Coupon[];
  finalPrice: number;
  totalDiscount: number;
}>(null);

const fetchCoupons = async () => {
  loading.value = true;
  error.value = null;
  try {
    coupons.value = await getCouponsApi();
  } catch (error_: any) {
    error.value = error_.message || "获取优惠券失败";
    console.error("Failed to fetch coupons", error_);
  } finally {
    loading.value = false;
  }
};

const handleClaim = async (coupon: Coupon) => {
  if (claimedCoupons.value.has(coupon.id)) return;

  claimingId.value = coupon.id;
  // Simulate API call
  await new Promise((resolve) => setTimeout(resolve, 800));

  claimedCoupons.value.add(coupon.id);
  claimingId.value = null;

  ElMessage({
    message: `恭喜！已成功领取：${coupon.title}`,
    type: "success",
    plain: true,
  });
};

const calculateBestPrice = () => {
  if (calcAmount.value <= 0) return;

  // Filter possible coupons based on platform and amount condition
  const eligible = coupons.value.filter((c) => {
    const platformMatch =
      calcPlatform.value === "ALL" || c.type === calcPlatform.value || c.type === "ALL_PLATFORM";
    const amountMatch = !c.condition_amount || calcAmount.value >= c.condition_amount;
    return platformMatch && amountMatch;
  });

  // Sort by amount descending to get biggest savings first
  const sorted = eligible.toSorted((a, b) => b.amount - a.amount);

  // Simple greedy selection: pick top 2 coupons
  const applied: Coupon[] = [];
  let currentDiscount = 0;

  for (const c of sorted) {
    if (applied.length < 2) {
      applied.push(c);
      currentDiscount += c.amount;
    }
  }

  calcResults.value = {
    appliedCoupons: applied,
    finalPrice: Number.parseFloat(Math.max(0, calcAmount.value - currentDiscount).toFixed(2)),
    totalDiscount: Number.parseFloat(currentDiscount.toFixed(2)),
  };
};

onMounted(() => {
  void fetchCoupons();
});

const platformMap: Record<string, string> = {
  ALL_PLATFORM: "全平台通用",
  JD_PLATFORM: "京东专享",
  PDD_PLATFORM: "拼多多专享",
  TMALL_PLATFORM: "天猫专享",
};

const getPlatformName = (type: string) => {
  return platformMap[type] || "特别优惠";
};

const getPlatformColor = (type: string) => {
  if (type.includes("JD")) return "bg-red-500";
  if (type.includes("TMALL") || type.includes("Tmall")) return "bg-orange-500";
  if (type.includes("PDD")) return "bg-red-600";
  return "bg-blue-600";
};
</script>

<template>
  <Page title="优惠计算中心" description="自动抓取全网最新优惠券，为您计算最佳到手价。">
    <div v-if="loading" class="flex justify-center items-center py-40">
      <span
        class="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full"
      ></span>
    </div>

    <div v-else-if="error" class="flex flex-col items-center justify-center py-20">
      <ElEmpty :description="error">
        <template #extra>
          <ElButton type="primary" @click="fetchCoupons">重试加载</ElButton>
        </template>
      </ElEmpty>
    </div>

    <div v-else-if="coupons.length === 0" class="flex flex-col items-center justify-center py-20">
      <ElEmpty description="当前暂无可用优惠券" />
    </div>
    <div v-else class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card
        v-for="coupon in coupons"
        :key="coupon.id"
        class="overflow-hidden border-none transition-all hover:scale-[1.02] hover:shadow-xl"
      >
        <div class="h-2" :class="[getPlatformColor(coupon.type)]"></div>
        <CardHeader class="pb-2">
          <div class="flex items-center justify-between">
            <Tag class="h-4 w-4 text-muted-foreground" />
            <span class="text-xs font-semibold text-muted-foreground">{{
              getPlatformName(coupon.type)
            }}</span>
          </div>
          <CardTitle class="text-xl font-bold line-clamp-1">{{ coupon.title }}</CardTitle>
        </CardHeader>
        <CardContent>
          <div class="flex items-center justify-between text-sm">
            <span class="text-primary font-bold text-lg">¥{{ coupon.amount }}</span>
            <span class="text-muted-foreground text-xs" v-if="coupon.condition_amount">满 ¥{{ coupon.condition_amount }} 可用</span>
          </div>
          <button
            class="mt-4 flex w-full items-center justify-center gap-2 rounded-lg py-2 text-sm font-medium shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            :class="[
              claimedCoupons.has(coupon.id)
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 border border-green-200 dark:border-green-800'
                : 'bg-primary text-primary-foreground hover:opacity-90',
            ]"
            @click="handleClaim(coupon)"
            :disabled="claimingId === coupon.id || claimedCoupons.has(coupon.id)"
          >
            <template v-if="claimingId === coupon.id">
              <span
                class="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full mr-1"
              ></span>
              领取中...
            </template>
            <template v-else-if="claimedCoupons.has(coupon.id)">
              <span class="iconify lucide--check w-4 h-4"></span>
              已领取
            </template>
            <template v-else>
              立即领取
              <ArrowRight class="h-4 w-4" />
            </template>
          </button>
        </CardContent>
      </Card>
    </div>

    <!-- 组合优惠计算器 -->
    <Card
      class="mt-8 border dark:border-zinc-800 bg-white/50 dark:bg-zinc-900/50 backdrop-blur-sm shadow-sm overflow-hidden"
    >
      <CardHeader>
        <div class="flex items-center gap-3">
          <div class="rounded-lg bg-primary/10 p-2 text-primary">
            <TicketPercent class="h-5 w-5" />
          </div>
          <CardTitle class="text-lg">组合优惠智能计算器</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div class="grid gap-6 md:grid-cols-3 items-end">
          <div class="space-y-2">
            <label class="text-xs font-medium text-muted-foreground ml-1">订单金额 (元)</label>
            <ElInputNumber
              v-model="calcAmount"
              :min="0"
              :precision="2"
              class="!w-full"
              placeholder="输入实付金额"
            />
          </div>
          <div class="space-y-2">
            <label class="text-xs font-medium text-muted-foreground ml-1">下单平台</label>
            <ElSelect v-model="calcPlatform" class="!w-full">
              <ElOption label="不限平台" value="ALL" />
              <ElOption label="京东 (JD)" value="JD_PLATFORM" />
              <ElOption label="天猫 (TMALL)" value="TMALL_PLATFORM" />
              <ElOption label="拼多多 (PDD)" value="PDD_PLATFORM" />
            </ElSelect>
          </div>
          <div>
            <ElButton
              type="primary"
              class="w-full !rounded-lg h-10 font-bold shadow-lg shadow-blue-500/20"
              @click="calculateBestPrice"
              :disabled="!calcAmount || coupons.length === 0"
            >
              立即智能计算
            </ElButton>
          </div>
        </div>

        <!-- 计算结果展示 -->
        <transition name="fade-slide">
          <div
            v-if="calcResults"
            class="mt-8 p-6 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10 border border-blue-100 dark:border-blue-900/30"
          >
            <div class="flex flex-col md:flex-row justify-between gap-6">
              <div class="space-y-4">
                <h4
                  class="text-sm font-bold text-blue-900 dark:text-blue-300 flex items-center gap-2"
                >
                  <span class="iconify lucide--sparkles w-4 h-4"></span>
                  推荐组合方案
                </h4>
                <div v-if="calcResults.appliedCoupons.length > 0" class="space-y-2">
                  <div
                    v-for="c in calcResults.appliedCoupons"
                    :key="c.id"
                    class="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-400"
                  >
                    <span class="iconify lucide--check-circle-2 w-4 h-4 text-green-500"></span>
                    <span class="font-medium">{{ c.title }}</span>
                    <span class="text-xs opacity-70">(-¥{{ c.amount }})</span>
                  </div>
                </div>
                <div v-else class="text-sm text-gray-500 flex items-center gap-2 italic">
                  <span class="iconify lucide--minus-circle w-4 h-4"></span>
                  当前条件下暂无可用优惠组合
                </div>
              </div>

              <div class="flex flex-col items-center md:items-end justify-center">
                <div class="text-xs text-muted-foreground mb-1 uppercase tracking-wider">
                  最佳预计到手价
                </div>
                <div class="text-4xl font-black text-blue-600 dark:text-blue-400">
                  ¥{{ calcResults.finalPrice }}
                </div>
                <div
                  class="mt-2 text-xs font-bold text-green-600 dark:text-green-500 inline-flex items-center gap-1 bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded"
                >
                  <span class="iconify lucide--arrow-down w-3 h-3"></span>
                  优惠已省 ¥{{ calcResults.totalDiscount }}
                </div>
              </div>
            </div>
          </div>
        </transition>
      </CardContent>
    </Card>
  </Page>
</template>
