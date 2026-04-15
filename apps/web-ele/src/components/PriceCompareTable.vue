<script setup lang="ts">
defineProps<{
  data?: any[];
}>();
</script>

<template>
  <div class="price-compare-table overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200 dark:divide-zinc-800">
      <thead class="bg-gray-50 dark:bg-zinc-800/50">
        <tr>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-zinc-400">平台</th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-zinc-400">当前价格</th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-zinc-400">库存状态</th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider dark:text-zinc-400">更新时间</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200 dark:bg-zinc-900 dark:divide-zinc-800">
        <tr v-for="(item, index) in data" :key="index" class="hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
          <td class="px-6 py-4 whitespace-nowrap dark:text-zinc-300">{{ item.platform }}</td>
          <td class="px-6 py-4 whitespace-nowrap text-red-600 font-medium dark:text-red-400">¥{{ item.price }}</td>
          <td class="px-6 py-4 whitespace-nowrap">
            <span :class="item.stock ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
              {{ item.stock ? '现货' : '缺货' }}
            </span>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-zinc-500">{{ item.updateTime }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
