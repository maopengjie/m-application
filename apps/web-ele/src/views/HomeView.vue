<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { Page } from "@vben/common-ui";

import { ArrowRight, Search, Sparkles, TrendingDown } from "lucide-vue-next";

import { AnalyticsEvents, logAnalyticsEventApi } from "#/api/analytics";
import { getProductListApi } from "#/api/product";
import ProductCard from "#/components/ProductCard.vue";

const router = useRouter();
const keyword = ref("");
const trendingProducts = ref<any[]>([]);
const loading = ref(true);

const handleSearch = () => {
  if (keyword.value.trim()) {
    void logAnalyticsEventApi(AnalyticsEvents.SEARCH_TRIGGERED, { q: keyword.value.trim() });
    router.push({
      name: "CommerceSearch",
      query: { q: keyword.value },
    });
  }
};

const fetchData = async () => {
  loading.value = true;
  try {
    const products = await getProductListApi({ limit: 8 });
    trendingProducts.value = products;
  } catch (error) {
    console.error("Failed to fetch dashboard data", error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  void fetchData();
});
</script>

<template>
  <Page>
    <div class="relative min-h-[calc(100vh-120px)] overflow-hidden bg-dot-pattern">
      <!-- Background Decorative Elements -->
      <div
        class="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-500/5 blur-[120px] rounded-full -z-10"
      ></div>

      <div class="max-w-6xl mx-auto px-6 pt-20 pb-12 space-y-20">
        <!-- Hero Section (Task H-01, H-02) -->
        <section class="text-center space-y-10">
          <div class="space-y-4 animate-in fade-in slide-in-from-top-4 duration-1000">
            <div
              class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold border border-blue-200 dark:border-blue-800 mx-auto"
            >
              <Sparkles class="h-3 w-3" />
              <span>智能决策引擎 V1.0 已就绪</span>
            </div>
            <h1 class="text-4xl md:text-5xl lg:text-6xl font-black tracking-tight leading-[1.1]">
              想买什么？<br />
              <span
                class="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-cyan-500"
              >
                输入商品或链接，剩下的交给 Decidely
              </span>
            </h1>
            <p class="text-md md:text-lg text-muted-foreground font-medium max-w-xl mx-auto">
              全网多平台实时比价 · 历史报价追踪 · AI 深度避雷分析
            </p>
          </div>

          <!-- Search Box (Core Task) -->
          <div
            class="relative max-w-2xl mx-auto group animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-200"
          >
            <div
              class="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl blur opacity-20 group-hover/search:opacity-30 transition duration-1000"
            ></div>
            <div
              class="relative bg-background rounded-2xl shadow-2xl p-2 flex items-center border-2 border-primary/10 transition-colors group/search"
            >
              <div class="flex-grow flex items-center px-4">
                <Search class="h-6 w-6 text-muted-foreground mr-3" />
                <input
                  v-model="keyword"
                  type="text"
                  placeholder="搜索手机、电脑、家电... 或粘贴京东/天猫商品链接"
                  class="w-full py-5 text-lg bg-transparent focus:outline-none placeholder:text-muted-foreground/50"
                  @keyup.enter="handleSearch"
                />
              </div>
              <button
                class="bg-primary hover:bg-primary/90 text-primary-foreground font-black px-10 py-5 rounded-xl transition-all shadow-lg active:scale-95 flex items-center gap-2"
                @click="handleSearch"
              >
                立即比价
                <ArrowRight class="h-5 w-5" />
              </button>
            </div>
          </div>

          <!-- Quick access chips -->
          <div
            class="flex flex-wrap justify-center gap-2 text-sm text-muted-foreground animate-in fade-in duration-1000 delay-300"
          >
            <span class="mr-2 self-center">正在热搜:</span>
            <button
              v-for="item in ['iPhone 15 Pro', 'RTX 4090', '扫地机器人', '戴森吹风机']"
              :key="item"
              class="px-4 py-1.5 rounded-full bg-secondary hover:bg-secondary/80 transition-colors font-medium border border-transparent hover:border-primary/20"
              @click="
                keyword = item;
                handleSearch();
              "
            >
              {{ item }}
            </button>
          </div>
        </section>

        <!-- Category Quick-Access (Task H-03) -->
        <div
          class="grid grid-cols-4 md:grid-cols-8 gap-6 animate-in fade-in duration-1000 delay-400"
        >
          <div
            v-for="(cat, idx) in [
              { name: '手机通讯', icon: 'smartphone' },
              { name: '数码IT', icon: 'monitor' },
              { name: '电脑办公', icon: 'laptop' },
              { name: '家用电器', icon: 'tv' },
              { name: '美妆个护', icon: 'sparkles' },
              { name: '户外运动', icon: 'bike' },
              { name: '图书音像', icon: 'book' },
              { name: '全部分类', icon: 'layout-grid' },
            ]"
            :key="idx"
            class="flex flex-col items-center gap-3 p-4 rounded-3xl hover:bg-white dark:hover:bg-zinc-800 hover:shadow-xl hover:-translate-y-1 transition-all cursor-pointer group"
            @click="
              keyword = cat.name === '全部分类' ? '' : cat.name;
              handleSearch();
            "
          >
            <div
              class="w-14 h-14 bg-background dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 rounded-2xl flex items-center justify-center text-zinc-400 group-hover:text-blue-600 group-hover:border-blue-100 transition-all shadow-sm"
            >
              <span :class="`iconify lucide--${cat.icon}`" class="text-2xl"></span>
            </div>
            <span
              class="text-xs font-bold text-zinc-600 dark:text-zinc-400 group-hover:text-blue-600 transition-colors"
              >{{ cat.name }}</span>
          </div>
        </div>

        <!-- Hot Drops (Task H-04) -->
        <div class="space-y-8 animate-in fade-in duration-1000 delay-500">
          <div class="flex items-center justify-between">
            <h2 class="text-2xl font-black flex items-center gap-3">
              <TrendingDown class="h-7 w-7 text-red-500" />
              今日热门降价
            </h2>
            <button
              class="text-sm font-bold text-blue-600 hover:underline flex items-center gap-1"
              @click="handleSearch"
            >
              查看更多 <ArrowRight class="h-3 w-3" />
            </button>
          </div>

          <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div v-for="i in 8" :key="i" class="h-80 bg-muted animate-pulse rounded-2xl"></div>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <ProductCard
              v-for="product in trendingProducts"
              :key="product.id"
              :product="product"
              @click="router.push({ name: 'CommerceDetail', params: { id: product.id } })"
            />
          </div>
        </div>

        <!-- Platform Ticker (Simplified) -->
        <div
          class="flex flex-wrap items-center justify-center gap-x-12 gap-y-6 pt-12 pb-20 border-t border-dashed opacity-30 grayscale hover:grayscale-0 transition-opacity"
        >
          <div
            v-for="p in ['京东', '天猫', '拼多多', '苏宁', '唯品会', '抖音电商']"
            :key="p"
            class="text-xs font-black tracking-[0.2em]"
          >
            {{ p }}
          </div>
        </div>
      </div>
    </div>
  </Page>
</template>

<style scoped>
.bg-background {
  background-color: hsl(var(--background));
}

.bg-dot-pattern {
  background-image: radial-gradient(hsl(var(--foreground) / 5%) 1px, transparent 1px);
  background-size: 32px 32px;
}
</style>
