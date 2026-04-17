<script setup lang="ts">
import type { Coupon } from "#/api/types";

import { onMounted, ref } from "vue";

import { Page } from "@vben/common-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@vben-core/shadcn-ui";

import { ArrowRight, Tag, TicketPercent } from "lucide-vue-next";

import { getCouponsApi } from "#/api/coupon";

const coupons = ref<Coupon[]>([]);
const loading = ref(true);
const error = ref<null | string>(null);

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

onMounted(() => {
  void fetchCoupons();
});

const getPlatformColor = (type: string) => {
  if (type.includes("JD")) return "bg-red-500";
  if (type.includes("Tmall")) return "bg-orange-500";
  return "bg-blue-500";
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
      <el-empty :description="error">
        <template #extra>
          <el-button type="primary" @click="fetchCoupons">重试加载</el-button>
        </template>
      </el-empty>
    </div>

    <div v-else-if="coupons.length === 0" class="flex flex-col items-center justify-center py-20">
      <el-empty description="当前暂无可用优惠券" />
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
            <span class="text-xs font-semibold uppercase text-muted-foreground">{{
              coupon.type
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
            class="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2 text-sm font-medium text-primary-foreground shadow-lg transition-all hover:opacity-90"
          >
            立即领取
            <ArrowRight class="h-4 w-4" />
          </button>
        </CardContent>
      </Card>
    </div>

    <!-- 组合优惠计算器占位 -->
    <Card class="mt-8 border-dashed border-2 bg-muted/20">
      <CardContent class="flex flex-col items-center justify-center py-12 text-center">
        <div class="rounded-full bg-primary/10 p-4 mb-4">
          <TicketPercent class="h-8 w-8 text-primary" />
        </div>
        <h3 class="text-lg font-semibold">组合优惠计算器</h3>
        <p class="text-sm text-muted-foreground max-w-md mt-2">
          输入您的购物车金额，我们将通过算法为您匹配最优的优惠叠加组合。
        </p>
      </CardContent>
    </Card>
  </Page>
</template>
