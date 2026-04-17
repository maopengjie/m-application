<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { Page } from "@vben/common-ui";

const router = useRouter();
const keyword = ref("");

const handleSearch = () => {
  if (keyword.value.trim()) {
    router.push({
      name: "CommerceSearch",
      query: { q: keyword.value },
    });
  }
};

const popularSearches = [
  "iPhone 15 Pro",
  "RTX 4090",
  "华为 Mate 60",
  "乐高 地平线",
  "米家 扫地机器人",
];
</script>

<template>
  <Page>
    <div
      class="min-h-[calc(100vh-200px)] flex flex-col items-center justify-center p-6 bg-gradient-to-b from-blue-50/50 to-white dark:from-zinc-900 dark:to-zinc-950 rounded-2xl"
    >
      <div class="max-w-2xl w-full text-center space-y-8 -mt-20">
        <!-- Mega Title -->
        <div class="space-y-4">
          <h1 class="text-5xl font-black text-gray-900 dark:text-zinc-100 tracking-tight">
            全网比价，<span class="text-blue-600">聪明</span>下单
          </h1>
          <p class="text-xl text-gray-500 dark:text-zinc-400 font-medium">
            聚合京东、天猫、拼多多等多平台数据，AI 助手为您保驾护航
          </p>
        </div>

        <!-- Search Box Area -->
        <div class="relative group">
          <div
            class="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000"
          ></div>
          <div
            class="relative bg-white dark:bg-zinc-900 rounded-2xl shadow-xl p-2 flex items-center border border-transparent dark:border-zinc-800"
          >
            <div class="flex-grow flex items-center px-4">
              <span class="iconify lucide--search text-gray-400 text-xl mr-3"></span>
              <input
                v-model="keyword"
                type="text"
                placeholder="输入商品名称、型号或搜索链接..."
                class="w-full py-4 text-lg bg-transparent focus:outline-none text-gray-800 dark:text-zinc-100"
                @keyup.enter="handleSearch"
              />
            </div>
            <button
              class="bg-blue-600 hover:bg-blue-700 text-white font-bold px-10 py-4 rounded-xl transition-all shadow-lg active:scale-95"
              @click="handleSearch"
            >
              立即探索
            </button>
          </div>
        </div>

        <!-- Popular Searches -->
        <div class="flex flex-wrap justify-center gap-3">
          <span class="text-sm text-gray-400 self-center mr-2">热门搜索:</span>
          <button
            v-for="tag in popularSearches"
            :key="tag"
            class="bg-white dark:bg-zinc-800 border dark:border-zinc-700 text-gray-600 dark:text-zinc-400 text-sm px-4 py-2 rounded-full hover:border-blue-500 hover:text-blue-500 transition-colors shadow-sm"
            @click="
              keyword = tag;
              handleSearch();
            "
          >
            {{ tag }}
          </button>
        </div>

        <!-- Features Brief -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12">
          <div
            class="bg-white/50 backdrop-blur-sm dark:bg-zinc-900/50 p-6 rounded-2xl border border-white/50 dark:border-zinc-800 shadow-sm text-left"
          >
            <div
              class="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl flex items-center justify-center mb-4"
            >
              <span class="iconify lucide--bar-chart-3"></span>
            </div>
            <h3 class="font-bold text-gray-900 dark:text-zinc-100 mb-1">历史价格</h3>
            <p class="text-xs text-gray-500 dark:text-zinc-400">
              追踪长达一年的价格起伏，识别“真假优惠”
            </p>
          </div>
          <div
            class="bg-white/50 backdrop-blur-sm dark:bg-zinc-900/50 p-6 rounded-2xl border border-white/50 dark:border-zinc-800 shadow-sm text-left"
          >
            <div
              class="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-xl flex items-center justify-center mb-4"
            >
              <span class="iconify lucide--zap"></span>
            </div>
            <h3 class="font-bold text-gray-900 dark:text-zinc-100 mb-1">AI 决策</h3>
            <p class="text-xs text-gray-500 dark:text-zinc-400">
              基于大数据分析，为您推荐最值得入手的时机
            </p>
          </div>
          <div
            class="bg-white/50 backdrop-blur-sm dark:bg-zinc-900/50 p-6 rounded-2xl border border-white/50 dark:border-zinc-800 shadow-sm text-left"
          >
            <div
              class="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-xl flex items-center justify-center mb-4"
            >
              <span class="iconify lucide--bell"></span>
            </div>
            <h3 class="font-bold text-gray-900 dark:text-zinc-100 mb-1">降价管家</h3>
            <p class="text-xs text-gray-500 dark:text-zinc-400">
              设置目标价，全天候监控，降价立刻通知您
            </p>
          </div>
        </div>
      </div>
    </div>
  </Page>
</template>
