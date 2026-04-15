<script lang="ts" setup>
import { onMounted, ref } from 'vue';

const loading = ref(true);

onMounted(() => {
  setTimeout(() => {
    loading.value = false;
  }, 800);
});

const data = [
  { name: 'Search Engine', value: 45, color: 'bg-blue-500' },
  { name: 'Direct', value: 25, color: 'bg-indigo-500' },
  { name: 'Social Media', value: 15, color: 'bg-purple-500' },
  { name: 'Referral', value: 10, color: 'bg-cyan-500' },
  { name: 'Others', value: 5, color: 'bg-gray-400' },
];
</script>

<template>
  <div class="p-2 min-h-[300px] flex flex-col justify-center">
    <div v-if="loading" class="flex flex-col items-center justify-center space-y-4">
      <div class="w-12 h-12 border-4 border-blue-600/20 border-t-blue-600 rounded-full animate-spin"></div>
      <p class="text-sm text-gray-500 animate-pulse">Loading analytics data...</p>
    </div>

    <div v-else class="space-y-6 transition-all duration-700 ease-in-out opacity-100 scale-100">
      <!-- Visual representation -->
      <div class="flex h-4 w-full rounded-full overflow-hidden shadow-inner bg-gray-100 dark:bg-zinc-800">
        <div 
          v-for="item in data" 
          :key="item.name"
          :class="[item.color, 'h-full transition-all duration-1000 ease-out']"
          :style="{ width: item.value + '%' }"
        ></div>
      </div>

      <!-- Legend and Stats -->
      <div class="grid grid-cols-1 gap-4">
        <div v-for="item in data" :key="item.name" class="flex items-center justify-between group cursor-default">
          <div class="flex items-center space-x-3">
            <div :class="[item.color, 'w-3 h-3 rounded-sm group-hover:scale-125 transition-transform shadow-sm']"></div>
            <span class="text-sm font-medium text-gray-700 dark:text-zinc-300">{{ item.name }}</span>
          </div>
          <div class="flex items-center space-x-4">
             <div class="w-24 h-1.5 bg-gray-100 dark:bg-zinc-800 rounded-full overflow-hidden hidden sm:block">
                <div :class="[item.color, 'h-full']" :style="{ width: item.value + '%' }"></div>
             </div>
             <span class="text-sm font-bold text-gray-900 dark:text-zinc-100 w-10 text-right">{{ item.value }}%</span>
          </div>
        </div>
      </div>

      <div class="pt-4 border-t border-gray-100 dark:border-zinc-800">
        <div class="flex justify-between items-center text-xs text-gray-500 dark:text-zinc-500">
          <span>Total Visits</span>
          <span class="font-medium text-gray-900 dark:text-zinc-200">28.4k</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.opacity-100 {
  opacity: 1;
}
.scale-100 {
  transform: scale(1);
}
</style>
