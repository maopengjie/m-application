<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">价格告警通知 center</h1>
    <div class="space-y-4">
      <div v-for="i in 3" :key="i" class="p-4 bg-white border-l-4 border-orange-400 shadow-sm rounded-r-lg flex items-center">
        <div class="mr-4 text-2xl">🔔</div>
        <div>
          <h4 class="font-bold">价格下跌提醒</h4>
          <p class="text-sm text-gray-600">您关注的元器件 "STM32F..." 已跌至设定阈值 ¥12.00 以下。</p>
          <span class="text-xs text-gray-400">2024-05-10 14:30:22</span>
        </div>
        <button class="ml-auto text-blue-600 text-sm">去处理</button>
      </div>
    </div>
  </div>
</template>
