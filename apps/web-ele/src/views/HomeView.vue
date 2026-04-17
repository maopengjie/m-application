<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { Page } from "@vben/common-ui";

import { Card, CardContent, CardHeader, CardTitle } from "@vben-core/shadcn-ui";

import {
  ArrowRight,
  BarChart3,
  Bell,
  Search,
  ShieldAlert,
  Sparkles,
  TicketPercent,
  TrendingDown,
  Zap,
} from "lucide-vue-next";

import { getCouponsApi } from "#/api/coupon";
import { getProductListApi } from "#/api/product";
import { getRisksApi } from "#/api/risk";

const router = useRouter();
const keyword = ref("");
const trendingProducts = ref<any[]>([]);
const risks = ref<any[]>([]);
const coupons = ref<any[]>([]);
const loading = ref(true);

const handleSearch = () => {
  if (keyword.value.trim()) {
    router.push({
      name: "CommerceSearch",
      query: { q: keyword.value },
    });
  }
};

const fetchData = async () => {
  loading.value = true;
  try {
    const [products, riskData, couponData] = await Promise.all([
      getProductListApi({ limit: 4 }),
      getRisksApi(),
      getCouponsApi(),
    ]);
    trendingProducts.value = products;
    risks.value = riskData.slice(0, 3);
    coupons.value = couponData.slice(0, 3);
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
    <div class="relative min-h-[calc(100vh-120px)] overflow-hidden">
      <!-- Background Decorative Elements -->
      <div
        class="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-blue-500/5 blur-[120px] rounded-full -z-10"
      ></div>
      <div
        class="absolute bottom-40 right-10 w-[400px] h-[400px] bg-purple-500/5 blur-[100px] rounded-full -z-10"
      ></div>

      <div class="max-w-7xl mx-auto px-6 py-12 lg:py-20 space-y-20">
        <!-- Hero Section -->
        <section class="max-w-4xl mx-auto text-center space-y-12">
          <div class="space-y-6 animate-in fade-in slide-in-from-top-4 duration-1000">
            <div
              class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold border border-blue-200 dark:border-blue-800"
            >
              <Sparkles class="h-3 w-3" />
              <span>AI 引擎已实时接入 3 大平台数据</span>
            </div>
            <h1 class="text-4xl md:text-6xl font-black tracking-tight leading-tight">
              全网聪明比价，<br />
              <span
                class="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-cyan-500"
              >
                让每一分钱都花在刀刃上
              </span>
            </h1>
            <p class="text-lg text-muted-foreground font-medium max-w-2xl mx-auto">
              Decidely 利用深度爬虫与 AI 模型，为您提供历史价格追踪、避雷分析及全量优惠方案。
            </p>
          </div>

          <!-- Search Box -->
          <div
            class="relative max-w-2xl mx-auto group animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-200"
          >
            <div
              class="absolute -inset-1 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-1000"
            ></div>
            <div class="relative bg-background rounded-2xl shadow-2xl p-2 flex items-center border">
              <div class="flex-grow flex items-center px-4">
                <Search class="h-5 w-5 text-muted-foreground mr-3" />
                <input
                  v-model="keyword"
                  type="text"
                  placeholder="搜索商品或粘贴购物链接..."
                  class="w-full py-4 text-base bg-transparent focus:outline-none"
                  @keyup.enter="handleSearch"
                />
              </div>
              <button
                class="hidden md:flex bg-primary hover:bg-primary/90 text-primary-foreground font-bold px-8 py-4 rounded-xl transition-all shadow-lg active:scale-95 items-center gap-2"
                @click="handleSearch"
              >
                探索底价
                <ArrowRight class="h-4 w-4" />
              </button>
            </div>
          </div>
        </section>

        <!-- Category Quick-Access -->
        <div
          class="grid grid-cols-4 md:grid-cols-8 gap-4 animate-in fade-in duration-1000 delay-300"
        >
          <div
            v-for="(cat, idx) in [
              { name: '数码IT', icon: 'monitor' },
              { name: '手机通讯', icon: 'smartphone' },
              { name: '家居生活', icon: 'home' },
              { name: '户外运动', icon: 'bike' },
              { name: '服饰箱包', icon: 'shopping-bag' },
              { name: '美妆个护', icon: 'sparkles' },
              { name: '食品生鲜', icon: 'utensils' },
              { name: '图书音像', icon: 'book' },
            ]"
            :key="idx"
            class="flex flex-col items-center gap-2 p-4 rounded-2xl hover:bg-white dark:hover:bg-zinc-800 hover:shadow-lg transition-all cursor-pointer group"
            @click="
              keyword = cat.name;
              handleSearch();
            "
          >
            <div
              class="w-12 h-12 bg-white dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 rounded-2xl flex items-center justify-center text-zinc-500 group-hover:text-blue-600 transition-colors shadow-sm"
            >
              <span :class="`iconify lucide--${cat.icon}`" class="text-xl"></span>
            </div>
            <span class="text-[11px] font-bold text-zinc-600 dark:text-zinc-400">{{
              cat.name
            }}</span>
          </div>
        </div>

        <!-- Platform Ticker / Trusted By -->
        <div
          class="flex flex-wrap items-center justify-center gap-x-12 gap-y-6 py-6 border-y border-dashed opacity-50 grayscale hover:grayscale-0 transition-all"
        >
          <div class="flex items-center gap-2 font-black text-xl italic text-red-600">
            JD <span class="text-[10px] not-italic font-bold">京东</span>
          </div>
          <div class="flex items-center gap-2 font-black text-xl italic text-orange-500">
            Tmall <span class="text-[10px] not-italic font-bold">天猫</span>
          </div>
          <div class="flex items-center gap-2 font-black text-xl italic text-red-500">
            PDD <span class="text-[10px] not-italic font-bold">拼多多</span>
          </div>
          <div class="flex items-center gap-2 font-black text-xl italic text-blue-500">
            Suning <span class="text-[10px] not-italic font-bold">苏宁</span>
          </div>
          <div
            class="flex items-center gap-2 font-black text-xl italic text-zinc-900 dark:text-zinc-100"
          >
            VIP <span class="text-[10px] not-italic font-bold">唯品会</span>
          </div>
        </div>

        <!-- Dynamic Insights Dashboard -->
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-2xl font-black flex items-center gap-2">
              <Zap class="h-6 w-6 text-blue-600" />
              今日实时情报
            </h2>
            <div
              class="flex items-center gap-4 text-xs font-bold text-muted-foreground bg-muted/30 px-4 py-2 rounded-full"
            >
              <div class="flex items-center gap-1.5">
                <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                引擎正常
              </div>
              <div class="flex items-center gap-1.5">
                活跃爬虫: <span class="text-blue-600 font-mono">124</span>
              </div>
              <div class="flex items-center gap-1.5">
                数据节点: <span class="text-blue-600 font-mono">42k/min</span>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <Card
              class="bg-background shadow-xl hover:shadow-2xl transition-all border-l-4 border-l-blue-500 overflow-hidden group"
            >
              <CardHeader
                class="flex flex-row items-center justify-between pb-2 bg-blue-50/30 dark:bg-blue-900/10"
              >
                <CardTitle class="text-[14px] font-black flex items-center gap-2">
                  <TrendingDown class="h-4 w-4 text-blue-500" />
                  今日降价榜
                </CardTitle>
              </CardHeader>
              <CardContent class="space-y-4 pt-4">
                <div
                  v-for="p in trendingProducts"
                  :key="p.id"
                  class="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                  @click="router.push({ name: 'CommerceDetail', params: { id: p.id } })"
                >
                  <img
                    :src="p.image_url"
                    class="h-10 w-10 rounded-lg border object-cover bg-white shadow-sm"
                  />
                  <div class="flex-grow min-w-0">
                    <div class="text-xs font-bold truncate">{{ p.title || p.name }}</div>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="text-xs font-mono font-bold text-blue-600">¥{{ p.current_price || p.price }}</span>
                      <span class="text-[10px] text-green-600 font-bold">↓ 12%</span>
                    </div>
                  </div>
                </div>
                <div v-if="loading" class="space-y-2">
                  <div
                    v-for="i in 3"
                    :key="i"
                    class="h-12 w-full bg-muted animate-pulse rounded-lg"
                  ></div>
                </div>
              </CardContent>
            </Card>

            <Card
              class="bg-background shadow-xl hover:shadow-2xl transition-all border-l-4 border-l-red-500 overflow-hidden group"
            >
              <CardHeader
                class="flex flex-row items-center justify-between pb-2 bg-red-50/30 dark:bg-red-900/10"
              >
                <CardTitle class="text-[14px] font-black flex items-center gap-2">
                  <ShieldAlert class="h-4 w-4 text-red-500" />
                  避雷红区 (AI 监测)
                </CardTitle>
              </CardHeader>
              <CardContent class="space-y-4 pt-4">
                <div
                  v-for="r in risks"
                  :key="r.id"
                  class="flex items-center gap-3 p-3 rounded-xl bg-red-50/50 dark:bg-red-950/20 border border-red-100 dark:border-red-900/50 hover:scale-[1.02] transition-transform"
                >
                  <div
                    class="h-8 w-8 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center text-red-600 dark:text-red-400 font-mono text-[10px] font-bold shadow-inner"
                  >
                    {{ r.score }}
                  </div>
                  <div class="flex-grow min-w-0">
                    <div class="text-[11px] font-black truncate">{{ r.sku_title }}</div>
                    <div class="text-[9px] text-red-600/70 font-bold uppercase tracking-wider">
                      Risk Level: High
                    </div>
                  </div>
                </div>
                <div v-if="loading" class="space-y-2">
                  <div
                    v-for="i in 2"
                    :key="i"
                    class="h-14 w-full bg-muted animate-pulse rounded-xl"
                  ></div>
                </div>
              </CardContent>
            </Card>

            <Card
              class="bg-background shadow-xl hover:shadow-2xl transition-all border-l-4 border-l-orange-500 overflow-hidden group"
            >
              <CardHeader
                class="flex flex-row items-center justify-between pb-2 bg-orange-50/30 dark:bg-orange-900/10"
              >
                <CardTitle class="text-[14px] font-black flex items-center gap-2">
                  <TicketPercent class="h-4 w-4 text-orange-500" />
                  超值神券
                </CardTitle>
              </CardHeader>
              <CardContent class="space-y-4 pt-4">
                <div
                  v-for="c in coupons"
                  :key="c.id"
                  class="group/coupon relative p-3 rounded-xl border-2 border-dashed border-orange-200 dark:border-orange-800 bg-orange-50/30 dark:bg-orange-950/10 hover:bg-orange-100 dark:hover:bg-orange-900/20 transition-all cursor-pointer"
                >
                  <div class="flex justify-between items-center">
                    <div>
                      <div class="text-sm font-black text-orange-600">¥{{ c.amount }}</div>
                      <div class="text-[10px] font-bold">{{ c.title }}</div>
                    </div>
                    <span
                      class="text-[10px] font-black px-2 py-1 rounded-lg bg-orange-600 text-white shadow-lg group-hover/coupon:scale-105 transition-transform"
                      >领</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <!-- How it works Timeline -->
        <section class="py-16 border-y bg-muted/20 -mx-6 px-6 relative overflow-hidden">
          <div
            class="absolute top-0 left-0 w-full h-full opacity-5 pointer-events-none"
            style="
              background-image: radial-gradient(#3b82f6 1px, transparent 1px);
              background-size: 20px 20px;
            "
          ></div>
          <div class="max-w-5xl mx-auto space-y-16 relative">
            <div class="text-center space-y-2">
              <h2 class="text-3xl font-black">如何三步完成底价下单？</h2>
              <p class="text-sm text-muted-foreground">
                Decidely 闭环购物引擎，为您的每一笔支出保驾护航
              </p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-16 relative">
              <div
                class="hidden md:block absolute top-12 left-[15%] right-[15%] h-0.5 border-b-2 border-dashed border-zinc-200 -z-10"
              ></div>

              <div
                v-for="(step, i) in [
                  {
                    title: '全网搜索/一键粘贴',
                    desc: '输入模糊关键词或直接粘贴任一平台商品链接。',
                    icon: 'search',
                    color: 'bg-blue-600',
                  },
                  {
                    title: '价格溯源/AI 研判',
                    desc: '秒级获取平台差价与历史走势，AI 给出入手建议。',
                    icon: 'zap',
                    color: 'bg-indigo-600',
                  },
                  {
                    title: '最优组合/降价订阅',
                    desc: '自动堆叠优惠，或设置降价提醒，等待底价时刻。',
                    icon: 'bell',
                    color: 'bg-orange-500',
                  },
                ]"
                :key="i"
                class="text-center group"
              >
                <div
                  :class="step.color"
                  class="w-24 h-24 rounded-3xl flex items-center justify-center mx-auto shadow-2xl group-hover:rotate-6 transition-transform relative ring-8 ring-white dark:ring-zinc-900"
                >
                  <span :class="`iconify lucide--${step.icon}`" class="text-3xl text-white"></span>
                  <div
                    class="absolute -top-3 -right-3 w-8 h-8 bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 rounded-full flex items-center justify-center font-black text-xs border-4 border-white dark:border-zinc-900"
                  >
                    0{{ i + 1 }}
                  </div>
                </div>
                <div class="mt-8 space-y-2">
                  <h4 class="font-black text-lg">{{ step.title }}</h4>
                  <p class="text-xs text-muted-foreground px-4 leading-relaxed">{{ step.desc }}</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- Static Features Brief -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            v-for="(f, i) in [
              {
                title: '历史价格',
                desc: '追踪长达一年的价格起伏，识别“真假优惠”',
                icon: BarChart3,
                color: 'text-blue-500',
                bg: 'bg-blue-100',
                route: 'CommerceSearch',
              },
              {
                title: 'AI 决策',
                desc: '基于大数据分析，为您推荐最值得入手的时机',
                icon: Zap,
                color: 'text-purple-500',
                bg: 'bg-purple-100',
                route: 'CommerceSearch',
              },
              {
                title: '降价管家',
                desc: '设置目标价，全天候监控，降价立刻通知您',
                icon: Bell,
                color: 'text-orange-500',
                bg: 'bg-orange-100',
                route: 'CommerceAlerts',
              },
            ]"
            :key="i"
            class="group p-8 rounded-3xl border bg-background/50 backdrop-blur hover:shadow-xl transition-all cursor-pointer hover:-translate-y-2"
            @click="router.push({ name: f.route })"
          >
            <div
              :class="[f.bg, f.color]"
              class="w-14 h-14 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-sm"
            >
              <component :is="f.icon" class="h-6 w-6" />
            </div>
            <h3 class="text-xl font-bold mb-3">{{ f.title }}</h3>
            <p class="text-sm text-muted-foreground leading-relaxed">{{ f.desc }}</p>
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
</style>
