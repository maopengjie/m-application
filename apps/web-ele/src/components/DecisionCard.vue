<script setup lang="ts">
import type { DecisionResult } from "#/api/types";

import { computed } from "vue";

const props = defineProps<{
  decision?: DecisionResult;
}>();

interface SuggestionInfo {
  label: string;
  color: string;
  bg: string;
  icon: string;
  actionClass: string;
}

const suggestionMap: Record<string, SuggestionInfo> = {
  BUY: {
    label: "建议购买",
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-50 dark:bg-green-900/20",
    icon: "lucide--check-circle",
    actionClass: "bg-green-600 hover:bg-green-700 shadow-green-500/20",
  },
  WAIT: {
    label: "建议等候",
    color: "text-orange-500 dark:text-orange-400",
    bg: "bg-orange-50 dark:bg-orange-900/20",
    icon: "lucide--clock",
    actionClass: "bg-orange-500 hover:bg-orange-600 shadow-orange-500/20",
  },
  AVOID: {
    label: "谨慎下单",
    color: "text-red-500 dark:text-red-400",
    bg: "bg-red-50 dark:bg-red-900/20",
    icon: "lucide--alert-octagon",
    actionClass: "bg-red-600 hover:bg-red-700 shadow-red-500/20",
  },
};

const currentSuggestion = computed(() => {
  return suggestionMap[props.decision?.suggestion || "WAIT"] || suggestionMap.WAIT;
});

const evidencePoints = computed(
  () =>
    props.decision?.evidence_text
      ?.split(/[；;]/)
      .map((s) => s.trim())
      .filter(Boolean) || [],
);
const riskPoints = computed(
  () =>
    props.decision?.risk_text
      ?.split(/[；;]/)
      .map((s) => s.trim())
      .filter(Boolean) || [],
);
</script>

<template>
  <div
    class="bg-white dark:bg-zinc-900 rounded-3xl border border-gray-100 dark:border-zinc-800 p-7 shadow-sm overflow-hidden relative flex flex-col h-full group"
  >
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
          <span class="iconify lucide--sparkles text-primary w-4 h-4"></span>
        </div>
        <h3
          class="font-black text-zinc-800 dark:text-zinc-100 uppercase tracking-widest text-[11px]"
        >
          Decidely AI 智能决策
        </h3>
      </div>
      <div class="flex flex-col items-end">
        <span class="text-xs font-black text-primary">{{ decision?.score || 0 }}</span>
        <span class="text-[8px] font-black text-zinc-400 uppercase tracking-tighter">AI 评分</span>
      </div>
    </div>

    <!-- 1. CONCLUSION (结论) -->
    <div
      class="rounded-3xl p-8 flex flex-col items-center justify-center text-center space-y-4 mb-8 transition-transform group-hover:scale-[1.02] duration-500"
      :class="[currentSuggestion?.bg]"
    >
      <div
        class="w-16 h-16 rounded-full flex items-center justify-center mb-2 bg-white dark:bg-zinc-900 shadow-xl shadow-black/5 border-2 border-white dark:border-zinc-800 relative"
      >
        <span
          class="iconify w-8 h-8"
          :class="[currentSuggestion.icon, currentSuggestion.color]"
        ></span>
        <div
          class="absolute -bottom-1 -right-1 w-6 h-6 bg-white dark:bg-zinc-800 rounded-full flex items-center justify-center shadow-sm border border-zinc-100 dark:border-zinc-700"
        >
          <span class="iconify lucide--brain-circuit text-[10px] text-primary"></span>
        </div>
      </div>
      <div>
        <div class="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-1">
          决策结论
        </div>
        <div class="text-4xl font-black tracking-tighter" :class="[currentSuggestion?.color]">
          {{ currentSuggestion?.label }}
        </div>
      </div>
      <div
        class="text-[11px] text-zinc-600 dark:text-zinc-300 font-bold leading-relaxed max-w-[220px]"
      >
        {{ decision?.reason || "系统正在深度挖掘价格与质量规律..." }}
      </div>
    </div>

    <!-- Details Section -->
    <div class="space-y-8 flex-grow">
      <!-- 2. EVIDENCE (证据) -->
      <div v-if="evidencePoints.length > 0" class="space-y-3">
        <div class="flex items-center justify-between">
          <div
            class="text-[10px] font-black text-zinc-400 uppercase tracking-widest flex items-center gap-2"
          >
            核心证据
          </div>
          <div
            v-if="decision?.evidence_delta_percent !== undefined"
            class="flex items-center gap-1.5"
          >
            <span class="text-[9px] font-black uppercase tracking-tighter text-zinc-400">距史低</span>
            <span
              class="text-[11px] font-black font-mono"
              :class="decision.evidence_delta_percent <= 0 ? 'text-green-500' : 'text-orange-500'"
            >
              {{ decision.evidence_delta_percent > 0 ? "+" : ""
              }}{{ decision.evidence_delta_percent }}%
            </span>
          </div>
        </div>
        <div class="space-y-2.5">
          <div
            v-for="point in evidencePoints"
            :key="point"
            class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300 flex items-start gap-2.5 leading-snug"
          >
            <div
              class="w-4 h-4 rounded-full bg-green-500/10 flex items-center justify-center mt-0.5 flex-shrink-0"
            >
              <span class="iconify lucide--check text-green-500 w-2.5 h-2.5"></span>
            </div>
            {{ point }}
          </div>
        </div>
      </div>

      <!-- 2.5 PRICE BREAKDOWN (价格构成 - R1-01, R1-04) -->
      <div class="space-y-4">
        <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest">
          价格构成分析
        </div>
        <div
          class="bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl p-4 border border-zinc-100 dark:border-zinc-800/50 space-y-3"
        >
          <div
            v-for="(detail, i) in decision?.discount_details"
            :key="i"
            class="flex justify-between items-center text-[11px]"
          >
            <span class="text-zinc-500 font-bold">{{ detail.split(":")[0] }}</span>
            <span class="font-black text-zinc-700 dark:text-zinc-300">{{
              detail.split(":")[1] || detail
            }}</span>
          </div>
          <div
            class="pt-2 mt-2 border-t border-dashed border-zinc-200 dark:border-zinc-700 flex justify-between items-center"
          >
            <span class="text-xs font-black text-zinc-800 dark:text-zinc-200">最终到手价</span>
            <span class="text-lg font-black text-red-600 font-mono">¥{{ decision?.final_price || decision?.original_price }}</span>
          </div>
          <div
            v-if="decision?.total_discount"
            class="text-[10px] text-right font-black text-primary"
          >
            已为您节省 ¥{{ decision.total_discount }}
          </div>
        </div>
      </div>

      <!-- 3. RISK (风险) -->
      <div v-if="riskPoints.length > 0" class="space-y-3">
        <div class="flex items-center justify-between">
          <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest">
            关键风险说明
          </div>
          <span
            class="iconify lucide--help-circle text-[10px] text-zinc-300 cursor-help"
            title="基于 AI 对评价、销量及价格波动的深度扫描"
          ></span>
        </div>
        <div
          class="bg-red-50/30 dark:bg-red-950/10 rounded-2xl p-4 border border-red-100/30 dark:border-red-900/10 space-y-2.5"
        >
          <div
            v-for="point in riskPoints"
            :key="point"
            class="text-[11px] font-bold text-red-600 dark:text-red-400 flex items-start gap-2.5 leading-snug"
          >
            <span class="iconify lucide--alert-triangle mt-0.5 flex-shrink-0 w-3 h-3"></span>
            {{ point }}
          </div>
        </div>
      </div>
    </div>

    <!-- 4. ACTION (动作) -->
    <div v-if="decision?.action_label" class="mt-8">
      <div
        class="text-white font-black text-center py-5 rounded-2xl shadow-xl transition-all active:scale-95 cursor-pointer text-sm tracking-wide"
        :class="[currentSuggestion.actionClass]"
      >
        {{ decision.action_label }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.tracking-tighter {
  letter-spacing: -0.05em;
}

.tracking-widest {
  letter-spacing: 0.1em;
}
</style>
