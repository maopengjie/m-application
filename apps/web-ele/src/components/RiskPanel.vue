<script setup lang="ts">
defineProps<{
  level?: 'low' | 'medium' | 'high';
  risks?: string[];
}>();
</script>

<template>
  <div class="risk-panel p-4 border rounded-lg bg-orange-50 border-orange-200 dark:bg-orange-950/20 dark:border-orange-900 transition-colors">
    <div class="flex items-center mb-3">
      <span class="font-bold text-orange-800 dark:text-orange-300">风险分析模块</span>
      <span class="ml-auto px-2 py-0.5 rounded text-xs text-white" 
            :class="{'bg-green-500 dark:bg-green-600': level === 'low', 'bg-orange-500 dark:bg-orange-600': level === 'medium', 'bg-red-500 dark:bg-red-600': level === 'high'}">
        {{ level?.toUpperCase() || 'MEDIUM' }}
      </span>
    </div>
    <ul class="text-sm text-orange-900 dark:text-orange-400 space-y-1">
      <li v-for="(risk, i) in risks" :key="i">⚠️ {{ risk }}</li>
    </ul>
  </div>
</template>
