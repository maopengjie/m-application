<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { Search } from '@element-plus/icons-vue';

const router = useRouter();
const query = ref('');

const handleSearch = () => {
  if (query.value.trim()) {
    router.push({ path: '/commerce/search', query: { q: query.value } });
  } else {
    router.push('/commerce/search');
  }
};
</script>

<template>
  <div class="min-h-[80vh] flex flex-col items-center justify-center p-6 bg-gradient-to-b from-white to-blue-50/30">
    <div class="max-w-4xl w-full text-center space-y-12">
      <!-- Hero Section -->
      <div class="space-y-4">
        <h1 class="text-5xl font-black text-gray-900 tracking-tight">
          找低价，做 <span class="text-blue-600">明智</span> 决策
        </h1>
        <p class="text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed">
          全网实时价格监测、历史走势分析、AI 采购建议，为您锁定每一个省钱机会。
        </p>
      </div>

      <!-- Search Box -->
      <div class="relative group max-w-2xl mx-auto">
        <div class="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
        <div class="relative bg-white p-2 rounded-2xl shadow-xl flex items-center gap-2">
          <div class="flex-1 flex items-center px-4">
            <el-icon class="text-gray-400 text-xl mr-3"><Search /></el-icon>
            <input 
              v-model="query" 
              type="text" 
              placeholder="输入元器件型号、手机、数码产品..." 
              class="w-full text-lg outline-none text-gray-800 placeholder-gray-400 py-3"
              @keyup.enter="handleSearch"
            >
          </div>
          <button @click="handleSearch" class="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg active:scale-95">
            立即开始
          </button>
        </div>
      </div>

      <!-- Features Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 pt-12">
        <div class="p-6 bg-white/60 backdrop-blur-sm rounded-2xl border border-white shadow-sm hover:shadow-md transition-all">
          <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center text-blue-600 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-zap"><path d="M4 14.75V3.5h16v11.25"/><path d="m16 9-4 4-4-4"/><path d="m3 12 3 3 4-4 4 4 7-7"/></svg>
          </div>
          <h3 class="font-bold text-gray-800 mb-2 text-left">价格追溯</h3>
          <p class="text-sm text-gray-500 text-left">提供过去 90 天的价格变动趋势，拒绝伪降价。</p>
        </div>
        <div class="p-6 bg-white/60 backdrop-blur-sm rounded-2xl border border-white shadow-sm hover:shadow-md transition-all">
          <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center text-purple-600 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-brain-circuit"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .52 8.208 4 4 0 0 0 6.97.228 3 3 0 1 0 1.033-6.136"/><path d="M9 21v-4"/><path d="M9 13v-2"/><path d="M8.4 16.3 7 15"/><path d="M12 5V2"/><path d="M11.5 8h-3"/></svg>
          </div>
          <h3 class="font-bold text-gray-800 mb-2 text-left">决策模型</h3>
          <h4 class="text-sm font-normal text-gray-500 text-left leading-relaxed">基于价格位点、优惠权重、渠道风险多维评分，给出购买建议。</h4>
        </div>
        <div class="p-6 bg-white/60 backdrop-blur-sm rounded-2xl border border-white shadow-sm hover:shadow-md transition-all">
          <div class="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center text-red-600 mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bell-ring"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/><path d="M4 2C2.8 3.7 2 5.7 2 8"/><path d="M22 8c0-2.3-.8-4.3-2-6"/></svg>
          </div>
          <h3 class="font-bold text-gray-800 mb-2 text-left">智能预警</h3>
          <p class="text-sm text-gray-500 text-left">设置您的心仪价位，一旦降价我们将第一时间告知。</p>
        </div>
      </div>
    </div>
  </div>
</template>
