<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  decision?: {
    score: number;
    suggestion: string;
    confidence: number;
    reason: string;
  }
}>();

const suggestionMap: any = {
  BUY: { label: '值得购买', color: 'text-green-600', bg: 'bg-green-50', icon: 'ri:checkbox-circle-fill' },
  WAIT: { label: '建议等待', color: 'text-orange-500', bg: 'bg-orange-50', icon: 'ri:time-fill' },
  AVOID: { label: '谨慎避雷', color: 'text-red-500', bg: 'bg-red-50', icon: 'ri:close-circle-fill' },
};

const currentSuggestion = computed(() => {
  return suggestionMap[props.decision?.suggestion || 'WAIT'];
});
</script>

<template>
  <div class="bg-white rounded-xl border p-6 shadow-sm overflow-hidden relative">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-bold text-gray-800">AI 购买决策</h3>
      <span class="text-xs text-gray-400">评分: {{ decision?.score || 0 }}</span>
    </div>

    <div :class="[currentSuggestion.bg, 'rounded-xl p-6 flex flex-col items-center justify-center text-center space-y-3']">
      <div :class="[currentSuggestion.color, 'text-4xl font-black']">
        {{ currentSuggestion.label }}
      </div>
      <div class="text-sm text-gray-600 font-medium">
        {{ decision?.reason || '系统正在计算最佳购买建议...' }}
      </div>
    </div>

    <div class="mt-6 space-y-2">
      <div class="flex justify-between text-xs">
        <span class="text-gray-500">置信度</span>
        <span class="font-bold text-gray-700">{{ (decision?.confidence || 0) * 100 }}%</span>
      </div>
      <el-progress :percentage="(decision?.confidence || 0.85) * 100" :show-text="false" :stroke-width="8" />
    </div>
  </div>
</template>
