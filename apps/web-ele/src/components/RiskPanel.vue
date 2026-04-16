<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  level?: 'low' | 'medium' | 'high';
  risks?: string[];
}>();

const config = computed(() => {
  const levels = {
    low: { bg: 'bg-green-50 dark:bg-green-950/20', border: 'border-green-100 dark:border-green-900/30', text: 'text-green-700 dark:text-green-400', label: '低风险', dot: 'bg-green-500' },
    medium: { bg: 'bg-orange-50 dark:bg-orange-950/20', border: 'border-orange-100 dark:border-orange-900/30', text: 'text-orange-700 dark:text-orange-400', label: '中风险', dot: 'bg-orange-500' },
    high: { bg: 'bg-red-50 dark:bg-red-950/20', border: 'border-red-100 dark:border-red-900/30', text: 'text-red-700 dark:text-red-400', label: '高风险', dot: 'bg-red-500' },
  };
  return levels[props.level || 'medium'];
});
</script>

<template>
  <div :class="[config.bg, config.border, 'p-5 border rounded-2xl transition-all']">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span :class="[config.dot, 'w-2 h-2 rounded-full']"></span>
        <span :class="[config.text, 'font-bold text-sm']">{{ config.label }}</span>
      </div>
      <span class="text-[10px] text-gray-400 dark:text-zinc-500 font-medium uppercase tracking-wider">Market Intelligence</span>
    </div>
    
    <div v-if="risks && risks.length" class="space-y-3">
      <div v-for="(risk, i) in risks" :key="i" class="flex gap-3 text-sm leading-relaxed">
        <span class="text-orange-400 mt-1">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
        </span>
        <span :class="config.text" class="font-medium opacity-90">{{ risk }}</span>
      </div>
    </div>
    <div v-else class="text-xs text-gray-400 dark:text-zinc-500 italic">
      当前商品暂无明显风险提示
    </div>
  </div>
</template>
