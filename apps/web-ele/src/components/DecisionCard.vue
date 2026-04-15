<script setup lang="ts">
defineProps<{
  decision?: string;
  advice?: string;
}>();
</script>

<template>
  <div class="decision-card p-5 bg-blue-50 border border-blue-100 rounded-xl dark:bg-blue-950/30 dark:border-blue-900 transition-colors">
    <h4 class="text-blue-800 font-bold mb-2 flex items-center dark:text-blue-300">
      <span class="mr-2">💡</span> 采购决策建议
    </h4>
    <p class="text-blue-900 font-medium text-lg mb-2 dark:text-blue-100">{{ decision || '建议分批次采购' }}</p>
    <p class="text-blue-700 text-sm italic dark:text-blue-400">{{ advice || '当前价格处于历史低位，但市场供应有紧缺趋势。' }}</p>
  </div>
</template>
