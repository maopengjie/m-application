<script setup lang="ts">
import type { RiskScore } from "#/api/types";

import { computed } from "vue";

const props = defineProps<{
  riskInfo?: RiskScore;
}>();

const level = computed(() => {
  const score = props.riskInfo?.score || 100;
  if (score < 40) return "high";
  if (score < 70) return "medium";
  return "low";
});

const config = computed(() => {
  const levels = {
    low: {
      bg: "bg-green-50/50 dark:bg-green-950/20",
      border: "border-green-100 dark:border-green-900/30",
      text: "text-green-700 dark:text-green-400",
      label: "安全系数高",
      icon: "lucide--shield-check",
      dot: "bg-green-500",
    },
    medium: {
      bg: "bg-orange-50/50 dark:bg-orange-950/20",
      border: "border-orange-100 dark:border-orange-900/30",
      text: "text-orange-700 dark:text-orange-400",
      label: "风险中等",
      icon: "lucide--help-circle",
      dot: "bg-orange-500",
    },
    high: {
      bg: "bg-red-50/50 dark:bg-red-950/20",
      border: "border-red-100 dark:border-red-900/30",
      text: "text-red-700 dark:text-red-400",
      label: "风险较高",
      icon: "lucide--shield-alert",
      dot: "bg-red-500",
    },
  };
  return levels[level.value];
});

const riskDetails = computed(() => {
  if (!props.riskInfo) return [];
  const details = [];
  if (props.riskInfo.price_abnormal) details.push("价格波动曲线存在异常跳变，谨防大数据杀熟");
  if (props.riskInfo.sales_abnormal) details.push("销量走势存在人行为干预迹象，数据真实度存疑");
  if (props.riskInfo.comment_abnormal)
    details.push("AI 语义分析识别到近期评价中质量相关负面词汇激增");
  if (props.riskInfo.rating_low) details.push("商家综合 DSR 评分显著低于行业均值，售后保障度较低");

  // Return either details or original details
  return details.length > 0 ? details : props.riskInfo.details || [];
});
</script>

<template>
  <div
    class="p-7 border-2 rounded-3xl transition-all h-full flex flex-col"
    :class="[config.bg, config.border]"
  >
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-xl bg-white dark:bg-zinc-900 shadow-sm">
          <span class="iconify w-5 h-5" :class="[config.icon, config.text]"></span>
        </div>
        <div class="flex flex-col">
          <span class="text-[9px] font-black text-zinc-400 uppercase tracking-widest">商家与市场风险</span>
          <span class="font-black text-sm" :class="[config.text]">{{ config.label }}</span>
        </div>
      </div>
      <div class="flex flex-col items-end">
        <span class="text-lg font-black font-mono leading-none" :class="[config.text]">{{
          riskInfo?.score || 100
        }}</span>
        <span class="text-[8px] font-black text-zinc-400 uppercase mt-1">分值安全度</span>
      </div>
    </div>

    <div class="space-y-4 flex-grow">
      <div v-if="riskDetails.length > 0" class="space-y-3">
        <div v-for="(risk, i) in riskDetails" :key="i" class="flex gap-3 text-xs leading-relaxed">
          <span class="mt-0.5 flex-shrink-0">
            <span class="iconify lucide--alert-triangle w-3 h-3 opacity-60"></span>
          </span>
          <span :class="config.text" class="font-black opacity-90">{{ risk }}</span>
        </div>
      </div>
      <div v-else class="flex flex-col items-center justify-center py-6 opacity-30">
        <span class="iconify lucide--check-circle w-6 h-6 mb-2"></span>
        <span class="text-[10px] font-black uppercase tracking-widest">未检测到显著异常</span>
      </div>
    </div>

    <div
      class="mt-6 pt-4 border-t border-dotted border-zinc-200 dark:border-zinc-800 flex justify-between items-center text-[9px] font-black text-zinc-400"
    >
      <span class="uppercase tracking-widest">Last Monitor</span>
      <span>{{ riskInfo?.updated_at || "刚刚" }}</span>
    </div>
  </div>
</template>

<style scoped>
.tracking-widest {
  letter-spacing: 0.1em;
}
</style>
