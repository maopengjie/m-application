<script setup lang="ts">
import { defineAsyncComponent } from "vue";
import { useRoute } from "vue-router";

import { Page } from "@vben/common-ui";

import {
  ElButton,
  ElEmpty,
  ElStatistic,
  ElTag,
} from "element-plus";

import { useProductDetail } from "#/views/use-product-detail";

const AlertDialog = defineAsyncComponent(() => import("#/components/AlertDialog.vue"));
const AlternativeProducts = defineAsyncComponent(
  () => import("#/components/AlternativeProducts.vue"),
);
const CouponPanel = defineAsyncComponent(() => import("#/components/CouponPanel.vue"));
const DecisionCard = defineAsyncComponent(() => import("#/components/DecisionCard.vue"));
const PriceCompareTable = defineAsyncComponent(() => import("#/components/PriceCompareTable.vue"));
const PriceTrendChart = defineAsyncComponent(() => import("#/components/PriceTrendChart.vue"));
const RiskPanel = defineAsyncComponent(() => import("#/components/RiskPanel.vue"));

const route = useRoute();
const productId = route.params.id as string;

const {
  alertDialogVisible,
  decision,
  decisionError,
  decisionLoading,
  error,
  handleAlertSubmit,
  handleBuy,
  handleCreateAlert,
  handleCreateAlertForSelectedSku,
  handleImageError,
  handleRetry,
  handleRetryDecision,
  handleSelectSku,
  loading,
  priceComparisonText,
  priceTrendText,
  product,
  ratingText,
  riskInfo,
  selectedShop,
  selectedSku,
  selectedSkuId,
  alternatives,
  isFollowed,
  isAlertSet,
  revisitSummary,
  handleFollow,
  handleUnfollow,
  // Intelligence
  intelligenceLoading,
  pricingAdvice,
  inventoryAnalysis,
  productInsight,
  handleExtractSpecs,
  handleAnalyzeReviews,
  generateInsight,
} = useProductDetail(productId);
</script>

<template>
  <Page
    :key="productId"
    :title="product?.name || '商品详情'"
    :description="product ? `品牌: ${product.brand || '未知'} | ID: ${product.id}` : ''"
  >
    <div v-loading="loading" class="min-h-[400px]">
      <div v-if="product" class="space-y-8">
        <!-- NEW: AI Synthesized Insight (Premium Header) -->
        <div
          v-if="productInsight"
          class="relative overflow-hidden bg-gradient-to-r from-zinc-900 to-zinc-800 dark:from-black dark:to-zinc-900 p-8 rounded-3xl text-white shadow-2xl border border-zinc-700/50"
        >
          <div class="absolute top-0 right-0 p-8 opacity-10">
            <span class="iconify lucide--brain-circuit w-32 h-32"></span>
          </div>
          <div class="relative z-10 flex flex-col md:flex-row gap-8 items-start">
            <div class="flex-grow space-y-4">
              <div class="flex items-center gap-2">
                <span
                  class="bg-primary text-primary-foreground text-[10px] font-black px-2 py-0.5 rounded uppercase tracking-widest"
                  >AI Agent Insight</span>
                <span class="text-[10px] text-zinc-400 font-bold">深度研判综述 · 实时更新</span>
              </div>
              <h2 class="text-xl font-black tracking-tight leading-relaxed">
                {{ productInsight }}
              </h2>
              <div class="flex gap-4">
                <div class="flex items-center gap-1.5 text-xs text-green-400 font-bold">
                  <span class="iconify lucide--check-circle w-3.5 h-3.5"></span>
                  全网多维验证
                </div>
                <div class="flex items-center gap-1.5 text-xs text-blue-400 font-bold">
                  <span class="iconify lucide--shield-check w-3.5 h-3.5"></span>
                  决策建议置信度 94%
                </div>
              </div>
            </div>
            <ElButton
              @click="generateInsight"
              :loading="intelligenceLoading"
              type="info"
              plain
              class="!bg-white/5 !border-white/10 !text-white !rounded-xl"
            >
              重新研判
            </ElButton>
          </div>
        </div>

        <!-- Hero / Recommendation Section -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <!-- Left: Product Image -->
          <div
            class="lg:col-span-4 bg-white dark:bg-zinc-900 p-8 rounded-3xl shadow-sm border border-gray-100 dark:border-zinc-800 flex items-center justify-center relative overflow-hidden group"
          >
            <div
              class="absolute -top-12 -left-12 w-48 h-48 bg-primary/5 blur-3xl rounded-full group-hover:bg-primary/10 transition-colors"
            ></div>
            <img
              :src="product.main_image"
              :alt="product.name"
              class="w-full h-auto aspect-square object-contain relative z-10 hover:scale-105 transition-transform duration-700"
              @error="handleImageError"
            />
          </div>

          <!-- Middle: Core Product Info & Price -->
          <div
            class="lg:col-span-5 bg-white dark:bg-zinc-900 p-8 rounded-3xl shadow-sm border border-gray-100 dark:border-zinc-800 flex flex-col justify-between"
          >
            <div class="space-y-6">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div
                    :class="selectedSku?.platform === 'JD' ? 'bg-red-600' : 'bg-orange-500'"
                    class="text-white text-[10px] font-black px-3 py-1 rounded-full shadow-lg"
                  >
                    {{ selectedSku?.platform || "未知渠道" }}
                  </div>
                  <span class="text-zinc-400 text-[10px] font-black uppercase tracking-tighter">{{
                    product.brand
                  }}</span>
                </div>
                <div class="flex items-center gap-1 text-[10px] text-zinc-400 font-bold">
                  ID: {{ product.id }}
                </div>
              </div>

              <div class="flex flex-wrap gap-2">
                <div
                  v-if="isFollowed"
                  class="bg-blue-500/10 text-blue-600 text-[10px] font-black px-3 py-1 rounded-full border border-blue-500/20 flex items-center gap-1 cursor-pointer hover:bg-blue-500/20 transition-colors"
                  @click="handleUnfollow"
                >
                  <span class="iconify lucide--heart w-3 h-3 fill-blue-600"></span>
                  正在关注中 (点击取消)
                </div>
                <div
                  v-else
                  class="bg-zinc-100 text-zinc-500 text-[10px] font-black px-3 py-1 rounded-full border border-zinc-200 flex items-center gap-1 cursor-pointer hover:bg-zinc-200 transition-colors"
                  @click="handleFollow"
                >
                  <span class="iconify lucide--heart w-3 h-3"></span>
                  加入关注
                </div>
                <div
                  v-if="isAlertSet"
                  class="bg-orange-500/10 text-orange-600 text-[10px] font-black px-3 py-1 rounded-full border border-orange-500/20 flex items-center gap-1"
                >
                  <span class="iconify lucide--bell-ring w-3 h-3"></span>
                  降价监测已开启
                </div>
              </div>

              <!-- Revisit Summary Block -->
              <div
                v-if="revisitSummary"
                class="p-4 rounded-2xl border flex flex-col gap-1 transition-all"
                :class="{
                  'bg-green-50/50 border-green-100 dark:bg-green-900/10 dark:border-green-800/20':
                    revisitSummary.type === 'success',
                  'bg-amber-50/50 border-amber-100 dark:bg-amber-900/10 dark:border-amber-800/20':
                    revisitSummary.type === 'warning',
                  'bg-blue-50/50 border-blue-100 dark:bg-blue-900/10 dark:border-blue-800/20':
                    revisitSummary.type === 'info',
                }"
              >
                <div
                  class="flex items-center gap-2"
                  :class="{
                    'text-green-600': revisitSummary.type === 'success',
                    'text-amber-600': revisitSummary.type === 'warning',
                    'text-blue-600': revisitSummary.type === 'info',
                  }"
                >
                  <span
                    :class="revisitSummary.icon || 'lucide:info'"
                    class="iconify w-4 h-4"
                  ></span>
                  <span class="text-[10px] font-black uppercase tracking-widest">{{
                    revisitSummary.title
                  }}</span>
                </div>
                <p class="text-xs font-bold text-zinc-600 dark:text-zinc-400 leading-relaxed">
                  {{ revisitSummary.content }}
                </p>
              </div>

              <h1 class="text-2xl font-black text-zinc-800 dark:text-zinc-100 leading-tight">
                {{ product.name }}
              </h1>

              <!-- Quick SKU Selector -->
              <div class="space-y-3">
                <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest">
                  选择渠道版本
                </div>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="sku in product.skus"
                    :key="sku.id"
                    class="px-3 py-2 rounded-xl border-2 transition-all flex items-center gap-2"
                    :class="
                      selectedSkuId === sku.id
                        ? 'border-primary bg-primary/5'
                        : 'border-zinc-100 dark:border-zinc-800 hover:border-primary/30'
                    "
                    @click="handleSelectSku(sku.id)"
                  >
                    <span class="text-[11px] font-black">{{ sku.platform }}: ¥{{ sku.final_price || sku.price }}</span>
                  </button>
                </div>
              </div>

              <!-- Price Visualization -->
              <div class="space-y-1 py-2">
                <div class="flex items-end gap-3">
                  <div class="flex flex-col">
                    <div class="flex items-center gap-2 mb-1 pl-1">
                      <span class="text-[10px] font-black text-red-600 uppercase tracking-widest">Decidely 预计到手价</span>
                      <div
                        v-if="decision"
                        class="bg-red-50 text-red-500 text-[8px] px-1.5 py-0.5 rounded-sm font-black uppercase tracking-tighter border border-red-100"
                      >
                        AI 计算
                      </div>
                    </div>
                    <div class="flex items-baseline gap-1">
                      <span class="text-xl font-black text-red-600 font-mono">¥</span>
                      <span class="text-5xl font-black text-red-600 tracking-tighter">{{
                        decision?.final_price || selectedSku?.final_price || selectedSku?.price
                      }}</span>
                    </div>
                  </div>
                  <div v-if="selectedSku?.price || decision?.original_price" class="mb-2">
                    <span class="text-zinc-400 line-through font-bold text-sm">¥{{ decision?.original_price || selectedSku?.price }}</span>
                    <div class="text-[10px] font-black text-primary uppercase">
                      立省 ¥{{
                        decision?.total_discount ||
                        (selectedSku?.original_price
                          ? selectedSku.original_price -
                            (selectedSku.final_price || selectedSku.price)
                          : 0
                        ).toFixed(0)
                      }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="flex flex-wrap gap-4 pt-2">
                <button
                  class="bg-primary hover:bg-primary/90 text-primary-foreground font-black px-12 py-5 rounded-2xl transition-all shadow-xl shadow-primary/20 active:scale-95 flex items-center gap-3 text-lg"
                  @click="handleBuy"
                >
                  <span class="iconify lucide--shopping-bag w-6 h-6"></span>
                  立即前往平台购买
                </button>
                <button
                  class="bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 font-black px-8 py-5 rounded-2xl transition-all active:scale-95 flex items-center gap-3"
                  @click="handleCreateAlertForSelectedSku"
                >
                  <span class="iconify lucide--bell-ring w-5 h-5"></span>
                  开启降价监测
                </button>
              </div>
            </div>

            <!-- Stats Ticker -->
            <div
              class="mt-8 pt-6 border-t border-dashed dark:border-zinc-800 grid grid-cols-3 gap-4"
            >
              <div class="space-y-1">
                <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest">
                  全网比价
                </div>
                <div class="text-xs font-black text-zinc-700 dark:text-zinc-300">
                  {{ priceComparisonText }}
                </div>
              </div>
              <div class="space-y-1">
                <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest">
                  价格水位
                </div>
                <div class="text-xs font-black text-zinc-700 dark:text-zinc-300">
                  {{ priceTrendText }}
                </div>
              </div>
              <div class="space-y-1">
                <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest">
                  购物口碑
                </div>
                <div class="text-xs font-black text-zinc-700 dark:text-zinc-300">
                  {{ ratingText }} 好评
                </div>
              </div>
            </div>
          </div>

          <!-- Right: AI Decision Center -->
          <div class="lg:col-span-3">
            <div v-loading="decisionLoading" class="h-full flex flex-col gap-6">
              <DecisionCard
                v-if="decision"
                :decision="decision"
                class="border-none shadow-none bg-blue-50/50 dark:bg-blue-900/10"
              />

              <!-- Alternative Recommendations -->
              <div
                v-if="
                  (decision?.suggestion === 'WAIT' || decision?.suggestion === 'AVOID') &&
                  alternatives.length > 0
                "
                class="flex-grow"
              >
                <AlternativeProducts :products="alternatives" />
              </div>

              <div
                v-else-if="decisionError"
                class="h-full bg-red-50 dark:bg-red-900/10 p-8 rounded-3xl flex flex-col items-center justify-center text-center"
              >
                <span class="iconify lucide--alert-triangle text-red-500 text-3xl mb-4"></span>
                <p class="text-red-500 text-sm font-bold mb-6">{{ decisionError }}</p>
                <ElButton
                  size="default"
                  type="primary"
                  class="!rounded-xl"
                  @click="handleRetryDecision"
                >
                  重试智能分析
                </ElButton>
              </div>
              <div
                v-else
                class="h-full bg-zinc-50 dark:bg-zinc-800/50 p-8 rounded-3xl border-2 border-dashed border-zinc-200 dark:border-zinc-700 flex flex-col items-center justify-center text-center text-zinc-400"
              >
                <div
                  class="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4"
                ></div>
                <div class="font-black text-sm">正在深度解析价格风险...</div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Intelligence Analysis Section -->
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <!-- AI Specification Center -->
          <div
            class="lg:col-span-3 bg-white dark:bg-zinc-900 p-8 rounded-3xl border border-gray-100 dark:border-zinc-800 shadow-sm"
          >
            <div class="flex items-center justify-between mb-8">
              <h3 class="text-lg font-black flex items-center gap-3">
                <span class="iconify lucide--sparkles text-amber-500"></span>
                AI 智能规格中心
              </h3>
              <ElButton
                :loading="intelligenceLoading"
                type="primary"
                plain
                class="!rounded-xl"
                @click="handleExtractSpecs"
              >
                手动触发 AI 提取
              </ElButton>
            </div>

            <div v-if="product.ai_attributes" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div
                v-for="(val, key) in product.ai_attributes"
                :key="key"
                class="p-4 bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl border border-zinc-100 dark:border-zinc-800"
              >
                <div class="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-1">
                  {{ key }}
                </div>
                <div class="text-sm font-black text-zinc-800 dark:text-zinc-100">{{ val }}</div>
              </div>
            </div>
            <div v-else class="py-10 text-center">
              <div class="text-zinc-400 text-sm font-bold mb-4">暂无 AI 提取的结构化规格</div>
              <p class="text-xs text-zinc-400 max-w-xs mx-auto">
                点击上方按钮，AI 将深度解析网页详情并自动为您提取关键技术参数。
              </p>
            </div>
          </div>

          <!-- Pricing & Sentiment Center -->
          <div class="space-y-6">
            <!-- Pricing Advice -->
            <div
              class="bg-gradient-to-br from-indigo-500 to-purple-600 p-8 rounded-3xl text-white shadow-xl"
            >
              <div class="flex items-center gap-2 mb-4">
                <span class="iconify lucide--trending-up w-5 h-5"></span>
                <span class="text-xs font-black uppercase tracking-widest">动态定价建议</span>
              </div>
              <div v-if="pricingAdvice" class="space-y-4">
                <div class="text-3xl font-black">¥{{ pricingAdvice.suggested_price }}</div>
                <div class="text-xs font-bold opacity-80 leading-relaxed">
                  {{ pricingAdvice.reason }}
                </div>
                <div class="pt-4 border-t border-white/10 flex justify-between items-center">
                  <span class="text-[10px] font-black uppercase opacity-60">市场最低参考</span>
                  <span class="text-sm font-black">¥{{ pricingAdvice.current_lowest_market_price }}</span>
                </div>
              </div>
              <div v-else class="text-xs font-bold opacity-60">正在计算全网最优价...</div>
            </div>

            <!-- Sentiment Analysis -->
            <div
              class="bg-white dark:bg-zinc-900 p-6 rounded-3xl border border-gray-100 dark:border-zinc-800"
            >
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2 text-zinc-800 dark:text-zinc-100">
                  <span class="iconify lucide--message-square w-4 h-4"></span>
                  <span class="font-black text-sm">用户评价情感</span>
                </div>
                <ElButton size="small" circle @click="handleAnalyzeReviews">
                  <span class="iconify lucide--refresh-cw"></span>
                </ElButton>
              </div>

              <div class="space-y-4">
                <div
                  v-for="review in selectedSku?.reviews?.slice(0, 3) || []"
                  :key="review.id"
                  class="space-y-1"
                >
                  <div class="flex items-center gap-2">
                    <ElTag
                      size="small"
                      :type="
                        review.sentiment_label === 'positive'
                          ? 'success'
                          : review.sentiment_label === 'negative'
                            ? 'danger'
                            : 'info'
                      "
                    >
                      {{ review.sentiment_label || "未分析" }}
                    </ElTag>
                    <span class="text-[10px] text-zinc-400">{{
                      review.created_at?.split("T")[0]
                    }}</span>
                  </div>
                  <p class="text-xs text-zinc-600 dark:text-zinc-400 line-clamp-2">
                    {{ review.content }}
                  </p>
                </div>
                <div
                  v-if="!selectedSku?.reviews?.length"
                  class="text-xs text-zinc-400 py-4 text-center"
                >
                  暂无评论数据
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Secondary Analysis Section -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 font-black">
          <!-- Left: Detailed Trends & Comparison -->
          <div class="lg:col-span-2 space-y-6">
            <!-- Price Trend -->
            <div
              class="bg-white dark:bg-zinc-900 p-8 rounded-3xl border border-gray-100 dark:border-zinc-800 shadow-sm"
            >
              <h3 class="text-lg font-black mb-8 flex items-center gap-3">
                <span class="iconify lucide--trending-down text-blue-500"></span>
                全周期价格趋势监测
              </h3>
              <PriceTrendChart :sku-id="selectedSku?.id" />
            </div>

            <!-- Shop Comparison -->
            <div
              class="bg-white dark:bg-zinc-900 p-8 rounded-3xl border border-gray-100 dark:border-zinc-800 shadow-sm"
            >
              <h3 class="text-lg font-black mb-8 flex items-center gap-3">
                <span class="iconify lucide--layout-grid text-purple-500"></span>
                全网实时比价分布
              </h3>
              <PriceCompareTable
                :data="product.skus || []"
                :selected-id="selectedSkuId ?? undefined"
                @create-alert="handleCreateAlert"
                @select="handleSelectSku"
              />
            </div>
          </div>

          <!-- Right: Insights & Alerts -->
          <div class="space-y-6">
            <!-- Coupon Panel -->
            <CouponPanel
              :coupons="selectedSku?.coupons || []"
              :current-price="selectedSku?.final_price || selectedSku?.price"
            />

            <!-- Risk Analysis -->
            <RiskPanel :risk-info="riskInfo" />

            <!-- Predictive Restock & Visual Tracking -->
            <div
              class="bg-zinc-50 dark:bg-zinc-800/50 p-6 rounded-3xl border border-zinc-100 dark:border-zinc-800"
            >
              <h4 class="text-xs font-black uppercase tracking-widest text-zinc-400 mb-4">
                库存预测与监控
              </h4>

              <div
                v-if="inventoryAnalysis"
                class="mb-6 p-4 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800"
              >
                <div class="flex items-center gap-2 mb-3">
                  <span class="iconify lucide--calendar-clock text-primary"></span>
                  <span class="text-[10px] font-black uppercase">补货预测建议</span>
                </div>

                <div v-if="inventoryAnalysis.status !== 'insufficient_data'">
                  <div class="flex justify-between items-end mb-4">
                    <ElStatistic
                      :value="inventoryAnalysis.estimated_days_remaining"
                      title="预计售完天数"
                    />
                    <ElTag
                      :type="
                        inventoryAnalysis.status === 'critical'
                          ? 'danger'
                          : inventoryAnalysis.status === 'warning'
                            ? 'warning'
                            : 'success'
                      "
                      size="small"
                    >
                      {{ inventoryAnalysis.status.toUpperCase() }}
                    </ElTag>
                  </div>
                  <div class="text-[10px] text-zinc-400 font-bold">
                    建议补货日期:
                    <span class="text-zinc-800 dark:text-zinc-100">{{
                      inventoryAnalysis.suggested_restock_date
                    }}</span>
                  </div>
                </div>
                <div v-else class="text-[10px] text-zinc-400 italic">
                  {{ inventoryAnalysis.message }}
                </div>
              </div>

              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-xs text-zinc-500">库存状态</span>
                  <ElTag
                    :type="selectedSku?.stock_status === 'in_stock' ? 'success' : 'danger'"
                    size="small"
                  >
                    {{ selectedSku?.stock_status === "in_stock" ? "充足" : "紧缺" }}
                  </ElTag>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-xs text-zinc-500">页面视觉指纹</span>
                  <span class="text-[10px] font-mono text-zinc-400">{{
                    selectedSku?.visual_hash?.slice(0, 8) || "N/A"
                  }}</span>
                </div>
                <div v-if="selectedSku?.last_screenshot" class="pt-2">
                  <img
                    :src="selectedSku.last_screenshot"
                    class="w-full h-20 object-cover rounded-xl opacity-50 grayscale hover:grayscale-0 transition-all"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error / Empty States -->
      <div v-else-if="error && !loading" class="flex flex-col items-center justify-center py-40">
        <ElEmpty :description="error">
          <template #extra>
            <div class="space-x-4">
              <ElButton @click="() => $router.back()">返回搜索</ElButton>
              <ElButton type="primary" @click="handleRetry">重新尝试</ElButton>
            </div>
          </template>
        </ElEmpty>
      </div>

      <!-- Alert Dialog -->
      <AlertDialog
        v-model="alertDialogVisible"
        :product="selectedShop || undefined"
        @submit="handleAlertSubmit"
      />
    </div>
  </Page>
</template>

<style scoped>
.tracking-widest {
  letter-spacing: 0.1em;
}

.tracking-tighter {
  letter-spacing: -0.05em;
}

.line-clamp-2 {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
