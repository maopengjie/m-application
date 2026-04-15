<script setup lang="ts">
import PriceCompareTable from '#/components/PriceCompareTable.vue';
import PriceTrendChart from '#/components/PriceTrendChart.vue';
import DecisionCard from '#/components/DecisionCard.vue';
import RiskPanel from '#/components/RiskPanel.vue';

const mockCompareData = [
  { platform: '立创商城', price: '12.45', stock: true, updateTime: '10分钟前' },
  { platform: '得捷电子', price: '13.10', stock: true, updateTime: '2小时前' },
  { platform: '贸泽电子', price: '12.80', stock: false, updateTime: '5分钟前' },
];
</script>

<template>
  <div class="p-6 space-y-6">
    <div class="flex items-center gap-4">
      <button class="text-blue-600">← 返回</button>
      <h1 class="text-2xl font-bold">STM32F103C8T6 详情分析</h1>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <div class="bg-white p-6 rounded-xl border shadow-sm">
          <h3 class="font-bold mb-4">价格走势分析</h3>
          <PriceTrendChart />
        </div>
        
        <div class="bg-white p-6 rounded-xl border shadow-sm">
          <h3 class="font-bold mb-4">全网比价</h3>
          <PriceCompareTable :data="mockCompareData" />
        </div>
      </div>

      <div class="space-y-6">
        <DecisionCard />
        <RiskPanel level="medium" :risks="['货源趋紧', '上游渠道涨价预期', '物流周期延长']" />
      </div>
    </div>
  </div>
</template>
