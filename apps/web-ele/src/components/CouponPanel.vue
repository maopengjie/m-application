<script setup lang="ts">
defineProps<{
  coupons?: any[];
}>();
</script>

<template>
  <div class="bg-white dark:bg-zinc-900 rounded-xl border border-gray-100 dark:border-zinc-800 p-6 shadow-sm">
    <div class="flex items-center gap-2 mb-4">
      <span class="iconify lucide--ticket text-orange-500"></span>
      <h3 class="font-bold text-gray-800 dark:text-zinc-100">当前可用优惠</h3>
    </div>

    <div v-if="coupons && coupons.length > 0" class="space-y-3">
      <div
        v-for="(coupon, index) in coupons"
        :key="index"
        class="relative flex items-center bg-orange-50 dark:bg-orange-900/10 border border-orange-100 dark:border-orange-950 rounded-lg p-3 overflow-hidden"
      >
        <div class="flex-shrink-0 text-orange-600 dark:text-orange-400 font-bold border-r border-orange-200 dark:border-orange-900/50 border-dashed pr-4 mr-4">
          <span class="text-xs">¥</span>
          <span class="text-2xl">{{ coupon.amount }}</span>
        </div>
        <div class="flex-grow">
          <div class="text-sm font-bold text-gray-800 dark:text-zinc-200">{{ coupon.title }}</div>
          <div class="text-xs text-gray-500 dark:text-zinc-500">{{ coupon.desc }}</div>
        </div>
        <el-button type="warning" size="small" plain round class="flex-shrink-0">领取</el-button>
        
        <!-- Decorative circles for ticket effect -->
        <div class="absolute -left-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-white dark:bg-zinc-900 rounded-full border border-orange-100 dark:border-orange-950"></div>
        <div class="absolute -right-2 top-1/2 -translate-y-1/2 w-4 h-4 bg-white dark:bg-zinc-900 rounded-full border border-orange-100 dark:border-orange-950"></div>
      </div>
    </div>
    
    <div v-else class="text-center py-6 text-gray-400 text-sm">
      目前没有可用优惠券
    </div>
  </div>
</template>
