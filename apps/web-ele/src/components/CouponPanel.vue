<script setup lang="ts">
import type { Coupon } from "#/api/types";

defineProps<{
  coupons?: Coupon[];
  currentPrice?: number;
}>();
</script>

<template>
  <div
    class="bg-white dark:bg-zinc-900 rounded-3xl border border-gray-100 dark:border-zinc-800 p-7 shadow-sm"
  >
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-2">
        <span class="iconify lucide--ticket text-orange-500 w-5 h-5"></span>
        <h3
          class="font-black text-zinc-800 dark:text-zinc-100 uppercase tracking-widest text-[11px]"
        >
          全网最优优惠券
        </h3>
      </div>
      <span
        class="text-[9px] font-black text-zinc-400 dark:text-zinc-500 bg-zinc-50 dark:bg-zinc-800 px-2 py-0.5 rounded-full"
        >实时同步</span>
    </div>

    <div v-if="coupons && coupons.length > 0" class="space-y-4">
      <div
        v-for="(coupon, index) in coupons"
        :key="index"
        class="relative flex items-center bg-orange-50/50 dark:bg-orange-900/10 border border-orange-100/50 dark:border-orange-950/30 rounded-2xl p-4 overflow-hidden group"
      >
        <!-- Coupon Value Area -->
        <div
          class="flex-shrink-0 text-orange-600 dark:text-orange-400 font-black border-r border-orange-200 dark:border-orange-900/30 border-dashed pr-4 mr-4 flex flex-col items-center justify-center min-w-[70px]"
        >
          <div>
            <span class="text-xs">¥</span>
            <span class="text-2xl tracking-tighter">{{ coupon.amount }}</span>
          </div>
          <span class="text-[9px] uppercase tracking-tighter opacity-70">优惠额度</span>
        </div>

        <!-- Coupon Info Area -->
        <div class="flex-grow">
          <div class="text-[11px] font-black text-zinc-800 dark:text-zinc-200 mb-0.5">
            {{ coupon.title }}
          </div>

          <!-- Decision Meta -->
          <div
            v-if="currentPrice"
            class="flex items-center gap-3 mt-1.5 pt-1.5 border-t border-orange-100 dark:border-orange-900/20 border-dotted"
          >
            <div class="flex flex-col">
              <span
                class="text-[8px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-tighter"
                >到手约</span>
              <span class="text-[12px] font-black text-orange-600 dark:text-orange-400 font-mono">¥{{ currentPrice - coupon.amount }}</span>
            </div>
            <div class="flex flex-col">
              <span
                class="text-[8px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-tighter"
                >立减</span>
              <span class="text-[12px] font-black text-green-600 dark:text-green-400 font-mono">-¥{{ coupon.amount }}</span>
            </div>
          </div>
          <div v-else class="text-[10px] text-zinc-400 font-bold opacity-70 mt-1">
            {{ coupon.desc || "领券购买更划算" }}
          </div>
        </div>

        <button
          class="bg-orange-500 hover:bg-orange-600 text-white text-[10px] font-black px-4 py-2 rounded-xl shadow-lg shadow-orange-500/20 transition-all flex-shrink-0 group-hover:scale-105"
        >
          领券
        </button>

        <!-- Ticket cutouts -->
        <div
          class="absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-white dark:bg-zinc-900 rounded-full border border-orange-100 dark:border-orange-950"
        ></div>
        <div
          class="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-white dark:bg-zinc-900 rounded-full border border-orange-100 dark:border-orange-950"
        ></div>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center py-10 opacity-30 grayscale">
      <span class="iconify lucide--ticket-slash w-8 h-8 mb-2"></span>
      <span class="text-[11px] font-black uppercase tracking-widest text-zinc-500">目前暂无叠加优惠</span>
    </div>
  </div>
</template>

<style scoped>
.tracking-widest {
  letter-spacing: 0.1em;
}

.tracking-tighter {
  letter-spacing: -0.05em;
}
</style>
